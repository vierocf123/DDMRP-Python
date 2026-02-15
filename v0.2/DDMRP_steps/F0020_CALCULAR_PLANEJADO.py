import pandas as pd
import numpy as np
import datetime as dt
import os


def calcular_range(v_dias_uteis,datas,data,tipo,dias,sentido,excludente,calcular_entrega:bool=False):
    
    """Calcular inicio e fim de um range de datas, baseando se em:
    - quantos dias deseja se cobrir no range (dias),
    - qual tipo de dias ("UTIL" x "CORRIDO")
    - em qual sentido se deseja ir apartir da data_ref (TRUE = futuro; FALSE = passado)
    - se deseja integrar a dataref na contagem ou não.
    
    v_dias_uteis = vetor de 0 e 1 representados as datas (0 - dia não util, 1 - dia util)
    datas = vetor de datas
    data = data_ref
    calcular_entrega = indica se caso o range extrapole o array deve-se inserir os valores na ultima célula (FALSE) ou desconsiderar (TRUE)"""
    
    #Pegar vetor posição da data de referencia
    referencia = datas.index(data)
    fim_range = len(v_dias_uteis)-1
    
    #Definir inicio, fim e sentido do range
    if excludente and sentido:
        inicio = referencia+1
        passo = 1
        fim = fim_range+1
        aux1 = 1
        aux2 = 0
    elif excludente and not(sentido):
        inicio = referencia-1
        passo = -1
        fim = -1
        aux1 = -1
        aux2 = 0
    elif not(excludente) and sentido:
        inicio = referencia
        passo = 1
        fim = fim_range+1
        aux1 = 1
        aux2 = -1
    elif not(excludente) and not (sentido):
        inicio = referencia
        passo = -1
        fim = -1
        aux1 = -1
        aux2 = 1
    
    soma_du = 0
    passos = 0
    
    #Calcular range em dias UTEIS
    if tipo == "UTIL":
        for i in range(inicio, fim, passo):
            soma_du += v_dias_uteis[i]
            passos += 1
            if soma_du >= dias:
                break
    #Calcular range em dias CORRIDOS
    else:
        passos = dias
    
    #Calcular fim
    fim = referencia + (passos*aux1) + aux2
    
    #Ajustar fim
    if (fim < 0):
        fim = 0
    elif (fim > fim_range) and not(calcular_entrega):
        fim = fim_range
    
    #Return
    return(inicio, fim)

def def_calcular_planejamento(data_ref, data_ref_consumo_i, data_ref_carteira_f, dias_bloqueados, data_f_projecao,
                              df_parametros, df_estoque, df_nips_saldo,
                              arr_consumo_demanda, arr_DAF, arr_reservas,
                              lista_materiais, df_demanda_atraso):

    """Calcula o planejamento do item DDMRP, define o ADU, parametros de variabilidade e Buffer. Em seguida,
    defina data de entrega e cria o vetor de datas de entrega."""

    """Define os ranges de datas para o range completo de consumo - demanda e o range de projeção"""

    #Datas DDMRP
    #Cria um conjunto de todas as datas do range
    datas_DDMRP_completo = pd.DataFrame({"DATA": pd.date_range(start=data_ref_consumo_i, end=data_ref_carteira_f, freq="D").date})
    #Remover datas bloqueadas
    datas_DDMRP_completo = datas_DDMRP_completo[~datas_DDMRP_completo["DATA"].isin(dias_bloqueados)].reset_index(drop=True)
    #Definir categoria do dia
    datas_DDMRP_completo["DIA_UTIL"] = pd.to_datetime(datas_DDMRP_completo["DATA"]).dt.weekday.map(lambda d: 0 if d >= 5 else 1)
    #Criar range de datas semanal
    datas_DDMRP_fluxo = datas_DDMRP_completo[(datas_DDMRP_completo["DATA"] >= data_ref) & (datas_DDMRP_completo["DATA"] <= data_f_projecao)]
    #Criar listas
    lista_DDMRP_fluxo = datas_DDMRP_fluxo["DATA"].tolist()
    lista_DDMRP_completo = datas_DDMRP_completo["DATA"].tolist()
    lista_DDMRP_fluxo_DIAS = np.array(datas_DDMRP_fluxo["DIA_UTIL"].tolist())
    lista_DDMRP_completo_DIAS = np.array(datas_DDMRP_completo["DIA_UTIL"].tolist())

    """Calcula ADU dos itens"""

    #Ordenar df_parametros por Material
    df_parametros.sort_values(by=['Material'], inplace=True)

    #Calcular Dados do Dia de Hoje
    df_parametros["MEDIA_CARTEIRA"] = 0
    df_parametros["DESV_CARTEIRA"] = 0
    df_parametros["MEDIA_CONSUMO"] = 0
    df_parametros["DESV_CONSUMO"] = 0
    df_parametros["ADU"] = 0
    df_parametros["DESV_ADU"] = 0
    df_parametros["DEMANDA_PICO"] = 0
    df_parametros["DEMANDA_HOJE"] = 0
    df_parametros["QTD_ATRASO_ADJ"] = 0
    df_parametros["DAF"] = 1
    df_parametros["DEMANDA_PF"] = 0
    df_parametros["DEMANDA_HOJE_REAL"] = 0
    
    #Para cada linha de df_dado_mestre
    for index, row in df_parametros.iterrows():
        
        #Ler atributos
        material = str(row["Material"])
        dias_consumo = int(row["DIAS_CONSUMO"])
        dias_demanda = int(row["DIAS_DEMANDA"])
        tipo_dia = str(row["TIPO_DIA"])
        dlt = int(row["DLT"])
        fator_dlt = float(row["FATOR DLT"])
        tipo_planejamento = str(row["TIPO_PLANEJAMENTO"])
        media_carteira = 0
        desv_carteira = 0
        media_consumo = 0
        desv_consumo = 0
        med_ADU = 0
        desv_ADU = 0
        DAF = 1
        demanda_pico = 0
        demanda_hoje = 0
        
        #Calcular ranges ADU

        if tipo_planejamento == "DDMRP":

            vetor_consumo = np.array([])
            vetor_demanda = np.array([])
            
            #Consumo
            if dias_consumo > 0:
                
                consumo_f, consumo_i = calcular_range(v_dias_uteis=lista_DDMRP_completo_DIAS,
                                                    datas=lista_DDMRP_completo,
                                                    data=data_ref,
                                                    tipo=tipo_dia,
                                                    dias=dias_consumo,
                                                    sentido=False,
                                                    excludente=True)
                
                vetor_consumo = np.concatenate((vetor_consumo, arr_consumo_demanda[index, consumo_i:consumo_f+1]))
                soma_consumo = np.sum(vetor_consumo)
                media_consumo = soma_consumo/dias_consumo
                desv_consumo = np.sqrt(np.sum((vetor_consumo - media_consumo)**2) / (dias_consumo - 1))
            
            #Demanda
            if dias_demanda > 0:
                
                carteira_i, carteira_f = calcular_range(v_dias_uteis=lista_DDMRP_completo_DIAS,
                                                        datas=lista_DDMRP_completo,
                                                        data=data_ref,
                                                        tipo=tipo_dia,
                                                        dias=dias_demanda,
                                                        sentido=True,
                                                        excludente=True)
                
                vetor_demanda = np.concatenate((vetor_demanda, arr_consumo_demanda[index, carteira_i:carteira_f+1]))
                soma_carteira = np.sum(vetor_demanda)
                media_carteira = soma_carteira/dias_demanda
                desv_carteira = np.sqrt(np.sum((vetor_demanda - media_carteira)**2) / (dias_demanda - 1))
            
            #Calcular parametros de ADU
            vetor_ADU = np.concatenate((vetor_consumo, vetor_demanda))
            med_ADU = np.sum(vetor_ADU)/(dias_consumo+dias_demanda)
            desv_ADU = np.sqrt(np.sum((vetor_ADU - med_ADU)**2) / (dias_consumo+dias_demanda - 1))
            
            #Atribuir DAF
            DAF = arr_DAF[index][0]
            
            #Calcular Demanda Hoje (RESERVAS HOJE + ATRASO)
            demanda_hoje = np.sum(arr_reservas[index,0:2])
            
            #Calcular Demanda Pico
            if dlt > 0:
                Y = DAF * med_ADU * dlt
                R1 = Y * fator_dlt
                limite_qtd = R1 + (DAF * med_ADU)
                damanda_pico_i, damanda_pico_f = calcular_range(v_dias_uteis=lista_DDMRP_fluxo_DIAS,
                                                                datas=lista_DDMRP_fluxo,
                                                                data=data_ref,
                                                                tipo=tipo_dia,
                                                                dias=dlt,
                                                                sentido=True,
                                                                excludente=True)
                reservas_range = arr_reservas[index, (damanda_pico_i+1):(damanda_pico_f+1)]
                reservas_range = arr_reservas[index,2:2+dlt]
                demanda_pico = reservas_range[reservas_range >= limite_qtd].sum()
            
            #Armazenar os valores na linha correspondente
            df_parametros.loc[index,"MEDIA_CARTEIRA"] = media_carteira
            df_parametros.loc[index,"DESV_CARTEIRA"] = desv_carteira
            df_parametros.loc[index,"MEDIA_CONSUMO"] = media_consumo
            df_parametros.loc[index,"DESV_CONSUMO"] = desv_consumo
            df_parametros.loc[index,"ADU"] = med_ADU
            df_parametros.loc[index,"DESV_ADU"] = desv_ADU
            df_parametros.loc[index,"DEMANDA_PICO"] = demanda_pico
            df_parametros.loc[index,"DEMANDA_HOJE"] = demanda_hoje
            df_parametros.loc[index,"DAF"] = DAF

        #Caso sejam itens PMP
        elif tipo_planejamento == "PMP":

            #Armazenar os valores na linha correspondente
            df_parametros.loc[index,"MEDIA_CARTEIRA"] = None
            df_parametros.loc[index,"DESV_CARTEIRA"] = None
            df_parametros.loc[index,"MEDIA_CONSUMO"] = None
            df_parametros.loc[index,"DESV_CONSUMO"] = None
            df_parametros.loc[index,"ADU"] = None
            df_parametros.loc[index,"DESV_ADU"] = None
            df_parametros.loc[index,"DEMANDA_PICO"] = None
            df_parametros.loc[index,"DEMANDA_HOJE"] = None

    """Calcular DAF"""

    #Calcular Demanda Ajustada por DAF
    df_parametros["ADU x DAF"] = df_parametros["ADU"]*df_parametros["DAF"]
    
    #Definir parametro de Variabilidade de Demanda
    df_parametros["TAXA VARIABILIDADE DA DEMANDA"] = np.where(df_parametros["ADU"] == 0,0,
                                                            df_parametros["DESV_ADU"] / df_parametros["ADU"])
    condicoes = [
        (df_parametros["ADU"] == 0),
        (df_parametros['TAXA VARIABILIDADE DA DEMANDA'] <= df_parametros["VAR LIM INF"]),
        (df_parametros['TAXA VARIABILIDADE DA DEMANDA'] <= df_parametros["VAR LIM SUP"]),
        (df_parametros['TAXA VARIABILIDADE DA DEMANDA'] > df_parametros["VAR LIM SUP"])]
    escolhas = [df_parametros["VAR M"],df_parametros["VAR L"], df_parametros["VAR M"], df_parametros["VAR H"]]
    df_parametros['FATOR VAR'] = np.select(condicoes, escolhas)
    escolhas = ["M","L","M","H"]
    df_parametros['HML'] = np.select(condicoes, escolhas)
    
    #Calcular Buffers
    df_parametros["Y"] = df_parametros["ADU x DAF"] * df_parametros["DLT"]
    df_parametros["R1"] = df_parametros["Y"] * df_parametros["FATOR DLT"]
    df_parametros["R2"] = df_parametros["FATOR VAR"] * df_parametros["R1"]
    df_parametros["R"] = df_parametros["R1"] + df_parametros["R2"]
    df_parametros["G1"] = df_parametros["TamMínLote"]
    df_parametros["G2"] = df_parametros["ADU x DAF"] * df_parametros["CICLO DESEJ."]
    df_parametros["G3"] = df_parametros["FATOR DLT"] * df_parametros["Y"]
    df_parametros["G"] = np.where(df_parametros["ADU"] == 0,0,df_parametros[['G1', 'G2', 'G3']].max(axis=1))
    df_parametros["TOR"] = df_parametros["R"]
    df_parametros["TOY"] = df_parametros["R"] + df_parametros["Y"]
    df_parametros["TOG"] = df_parametros["TOY"] + df_parametros["G"]
    
    #Remover colunas desnecessarias
    df_parametros = df_parametros.drop(columns=['VAR LIM INF','VAR LIM SUP', 'VAR L', 'VAR M', 'VAR H'])

    #Calcular Fluxo Liquido e NIP Sugerida
    
    #Unir informaçãoes de NIPs e Estoque
    df_parametros = df_parametros.merge(df_estoque, on='Material', how='left')
    df_parametros = df_parametros.merge(df_nips_saldo, on='Material', how='left')
    df_parametros = df_parametros.drop(columns=['Qtd.Kanban']).rename(columns={'SALDO': 'ESTOQUE',
                                                                            'Qtd.plan.': 'NIPs'})
    df_parametros['ESTOQUE'] = df_parametros['ESTOQUE'].fillna(0)
    df_parametros['NIPs'] = df_parametros['NIPs'].fillna(0)

    #Calcular Fluxo Liquido
    df_parametros['FLUXO_LIQUIDO'] = np.where(df_parametros['TIPO_MATERIAL'] == 'PRODUTO-PRONTO',
                                            df_parametros['ESTOQUE'] + df_parametros['NIPs'] + df_parametros['DEMANDA_PICO'],
                                            df_parametros['ESTOQUE'] + df_parametros['NIPs'])
    #Calcular Prioridade%
    df_parametros["PRIORIDADE%"] = np.where(df_parametros["ADU"] == 0,1,
                                            df_parametros["FLUXO_LIQUIDO"] / df_parametros["TOG"])
    #Calcular NIP SUGERIDA
    df_parametros['NIP_SUGERIDA'] = np.where((df_parametros['ADU']>0) & ((df_parametros['FLUXO_LIQUIDO'] <= df_parametros['TOY']) | (df_parametros['FLUXO_LIQUIDO'] > df_parametros['TOG'])),
                                            df_parametros['TOG'] - df_parametros['FLUXO_LIQUIDO'],0).round(0).astype(int)

    #Definir data de entrega
    df_parametros["DATA_ENTREGA"] = None

    #Inserir informações de demanda em atraso
    df_parametros = df_parametros.merge(df_demanda_atraso,
                                        how='left',
                                        left_on='Material',
                                        right_on='Material')
    df_parametros["ATRASO"] = df_parametros["ATRASO"].fillna(0)
    df_parametros = df_parametros.rename(columns={"ATRASO": "CARTEIRA_EM_ATRASO"})

    #Para cada linha de df_parametros
    for index, row in df_parametros.iterrows():
        
        #Ler atributos
        dlt = int(row["DLT"])
        qtd_nip = row["NIP_SUGERIDA"]
        tipo_dia = str(row["TIPO_DIA"])
        
        #Se houver NIPs para Sugerida
        if qtd_nip > 0:
            indice_i, indice_f = calcular_range(v_dias_uteis=lista_DDMRP_completo_DIAS,
                                                datas=lista_DDMRP_completo,
                                                data=data_ref,
                                                tipo=tipo_dia,
                                                dias=dlt,
                                                sentido=True,
                                                excludente=False)
            df_parametros.loc[index,"DATA_ENTREGA"] = lista_DDMRP_completo[indice_f]

    #Criar Vetores de Planejamento e de Entrega do Planejado
    df_planejado_entrega = df_parametros[["Material", "NIP_SUGERIDA", "DATA_ENTREGA"]]
    df_planejado_entrega = df_planejado_entrega.rename(columns={"NIP_SUGERIDA": "Qtd", "DATA_ENTREGA": "Data"})
    df_planejado_entrega = df_planejado_entrega[df_planejado_entrega['Qtd'] > 0]
    df_planejado = df_planejado_entrega[["Material", "Qtd"]]
    df_planejado["Data"] = data_ref
    
    #Cria grid de Material x Data
    datas = pd.date_range(start=data_ref, end=data_f_projecao, freq="D").date
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "Data"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_planejado_entrega = (df_grid.merge(df_planejado_entrega, on=["Material", "Data"], how="left").fillna({"Qtd": 0}))
    df_planejado = (df_grid.merge(df_planejado, on=["Material", "Data"], how="left").fillna({"Qtd": 0}))
    
    #Garante que QTD é numérico
    df_planejado_entrega["Qtd"] = df_planejado_entrega["Qtd"].astype(float)
    df_planejado["Qtd"] = df_planejado["Qtd"].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_planejado_entrega = df_planejado_entrega[~df_planejado_entrega["Data"].isin(dias_bloqueados)].reset_index(drop=True)
    df_planejado = df_planejado[~df_planejado["Data"].isin(dias_bloqueados)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_planejado_entrega = df_planejado_entrega.sort_values(by=['Material', 'Data'])
    df_planejado = df_planejado.sort_values(by=['Material', 'Data'])
    
    #Agrupar valores
    df_planejado_entrega = (df_planejado_entrega.groupby(['Material', 'Data'], as_index=False)["Qtd"].sum())
    df_planejado = (df_planejado.groupby(['Material', 'Data'], as_index=False)["Qtd"].sum())
    
    #Pivot Tables
    df_planejado = df_planejado.pivot(index=['Material'], columns='Data', values='Qtd')
    df_planejado_entrega = df_planejado_entrega.pivot(index=['Material'], columns='Data', values='Qtd')
    
    #Transformar df_planejado_entrega e df_planejado em array
    arr_planejado = df_planejado.to_numpy()
    arr_planejado_entrega = df_planejado_entrega.to_numpy()

    #Retornar Dataframe de parametros com Planejamento e vetores do planejamento
    return(df_parametros, arr_planejado, arr_planejado_entrega, lista_DDMRP_fluxo, lista_DDMRP_completo, lista_DDMRP_fluxo_DIAS, lista_DDMRP_completo_DIAS)