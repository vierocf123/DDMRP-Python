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

def def_calcular_projecao(data_ref, lista_DDMRP_completo, lista_DDMRP_completo_DIAS,
                          lista_DDMRP_fluxo, lista_DDMRP_fluxo_DIAS, df_parametros,
                          arr_planejado_entrega, arr_consumo_demanda, arr_NIPs, arr_planejado, arr_DAF):

    """Calcula a projeção dos itens baseado nos parametros do planejado e buffers calculados para
    cada dia do range.
    
    Retorna: arrays de informações calculadas para cada dia da projeção."""

    #Criar novos arrays vazios
    arr_ADU = []
    arr_TOG = []
    arr_TOY = []
    arr_TOR = []
    arr_DEMANDA_QUALIFICADA = []
    arr_ESTOQUE = []
    arr_FLUXO_LIQUIDO = []
    arr_PLANEJADO_PROJECAO = np.zeros((len(arr_planejado_entrega), len(arr_planejado_entrega[0])))
    indice = lista_DDMRP_completo.index(data_ref)
    
    #Para cada linha de df_parametros
    for index, row in df_parametros.iterrows():
        
        #Arrays Auxiliares
        arr_ADU_aux = []
        arr_TOG_aux = []
        arr_TOY_aux = []
        arr_TOR_aux = []
        arr_DEMANDA_QUALIFICADA_aux = []
        arr_ESTOQUE_aux = []
        arr_FLUXO_LIQUIDO_aux = []
        
        #Ler parametros do item
        material = str(row["Material"])
        dias_consumo = int(row["DIAS_CONSUMO"])
        dias_demanda = int(row["DIAS_DEMANDA"])
        tipo_dia = str(row["TIPO_DIA"])
        dlt = int(row["DLT"])
        fator_dlt = float(row["FATOR DLT"])
        adu_fixa = str(row["ADU_FIXA"])
        adu = float(row["ADU"])
        fator_var = float(row["FATOR VAR"])
        tamanho_lote_min = float(row["TamMínLote"])
        ciclo_desejado = float(row["CICLO DESEJ."])
        TOG = float(row["TOG"])
        TOY = float(row["TOY"])
        TOR = float(row["TOR"])
        R1 = float(row["R1"])
        
        #Parametros de loop
        i = 1
        
        #Estoque = Estoque - Demanda Hoje + NIPs Hoje + NIPs Atraso
        estoque = float(row["ESTOQUE"]) - (arr_consumo_demanda[index][indice]) + np.sum((arr_NIPs[index][0:2]))
        
        #NIP_ACUMULADA = Todas as NIPs + Planejado Hoje - Entrega Hoje - Entrega Atraso
        NIP_ACUMULADA = float(row["NIPs"]) + arr_planejado[index][0] - np.sum((arr_NIPs[index][0:2]))
        
        #Para cada data em 
        for data_ref_fluxo in lista_DDMRP_fluxo[1:]:
            
            #Ler parametros do item na Data
            daf = arr_DAF[index][i]
            
            #Se a ADU NÃO for FIXA
            if adu_fixa != "S":
                
                #Calcular ADU
                vetor_consumo = np.array([])
                vetor_demanda = np.array([])
                
                #Consumo
                if dias_consumo > 0:
                    consumo_f, consumo_i = calcular_range(v_dias_uteis=lista_DDMRP_completo_DIAS,
                                                        datas=lista_DDMRP_completo,
                                                        data=data_ref_fluxo,
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
                                                            data=data_ref_fluxo,
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
                adu = np.sum(vetor_ADU)/(dias_consumo+dias_demanda)
                
                #Calcular Buffer (G, Y, R)   
                Y = adu * dlt * daf
                R1 = Y * fator_dlt
                R2 = R1 * fator_var
                R = R1 + R2
                G1 = tamanho_lote_min
                G2 = adu * daf * ciclo_desejado
                G3 = fator_dlt * Y
                G = 0 if (adu==0) else max(G1, G2, G3)
                TOR = R
                TOY = R + Y
                TOG = R + Y + G
                
                #Calcular Demanda Pico & Demanda Pico
                limite_qtd = R1 * adu
                damanda_pico_i, damanda_pico_f = calcular_range(v_dias_uteis=lista_DDMRP_completo_DIAS,
                                                                datas=lista_DDMRP_completo,
                                                                data=data_ref_fluxo,
                                                                tipo=tipo_dia,
                                                                dias=dlt,
                                                                sentido=True,
                                                                excludente=True)
                demanda_pico_range = arr_consumo_demanda[index, (damanda_pico_i):(damanda_pico_f)]
                demanda_pico = demanda_pico_range[demanda_pico_range >= limite_qtd].sum()
                demanda_qualificada = demanda_pico + arr_consumo_demanda[index][damanda_pico_i-1]
                demanda_qualificada = demanda_qualificada * daf
            
            #Se a ADU for FIXA
            else:
                
                #Calcular Demanda Qualificada
                demanda_qualificada = adu * daf
            
            #Calcular Projeção
            #Atualizar NIP_ACUMULADA = NIP_ACUMULADA - NIPs HOJE - PLANEJADOS ENTREGUES HOJE
            NIP_ACUMULADA = NIP_ACUMULADA - arr_NIPs[index][i+1] - arr_planejado_entrega[index][i]
            
            #Atualizar ESTOQUE = ESTOQUE + NIPs HOJE + PLANEJADOS ENTREGUES HOJE
            estoque = estoque + arr_NIPs[index][i+1] + arr_planejado_entrega[index][i]
            
            #FLUXO LIQUIDO = NIP_ACUMULADA + ESTOQUE - DEMANDA_QUALIFICADA
            fluxo_liquido = NIP_ACUMULADA + estoque - demanda_qualificada
            
            #CALCULAR NIP e ARMAZENAR
            if (fluxo_liquido < TOY) and (adu > 0) and (dlt > 0):
                
                #Calcular NIP
                NIP = TOG - fluxo_liquido
                
                #Atualizar NIP_ACUMULADA com nova NIP
                NIP_ACUMULADA = NIP_ACUMULADA + NIP
                
                #Armazenar NIP em arr_planejado 
                arr_planejado[index][i] = arr_planejado[index][i] + NIP
                
                #Armazenar NIP em arr_planejado_entrega
                indice_nip_i, indice_nip_f = calcular_range(v_dias_uteis=lista_DDMRP_fluxo_DIAS,
                                                            datas=lista_DDMRP_fluxo,
                                                            data=data_ref_fluxo,
                                                            tipo=tipo_dia,
                                                            dias=dlt,
                                                            sentido=True,
                                                            excludente=False,
                                                            calcular_entrega=True)
                if indice_nip_f <= len(arr_planejado_entrega[index][:])-1:
                    arr_planejado_entrega[index][indice_nip_f] = arr_planejado_entrega[index][indice_nip_f] + NIP
                    arr_PLANEJADO_PROJECAO[index][indice_nip_f] = arr_PLANEJADO_PROJECAO[index][indice_nip_f] + NIP
            else:
                NIP = 0
            
            #Se a ADU NÃO for FIXA
            if adu_fixa != "S":
                
                #Atualizar Estoque - Demanda Hoje
                estoque = estoque - arr_consumo_demanda[index][indice+i]
            
            else:
                
                #Atualizar Estoque - Demanda Qualificada
                estoque = estoque - demanda_qualificada
            
            #Inserir dados diarios
            arr_ADU_aux.append(adu)
            arr_TOG_aux.append(TOG)
            arr_TOY_aux.append(TOY)
            arr_TOR_aux.append(TOR)
            arr_DEMANDA_QUALIFICADA_aux.append(demanda_qualificada)
            arr_ESTOQUE_aux.append(estoque)
            arr_FLUXO_LIQUIDO_aux.append(fluxo_liquido)
            i = i + 1
        
        #Inserir dados range
        arr_ADU.append(arr_ADU_aux)
        arr_TOG.append(arr_TOG_aux)
        arr_TOY.append(arr_TOY_aux)
        arr_TOR.append(arr_TOR_aux)
        arr_DEMANDA_QUALIFICADA.append(arr_DEMANDA_QUALIFICADA_aux)
        arr_ESTOQUE.append(arr_ESTOQUE_aux) 
        arr_FLUXO_LIQUIDO.append(arr_FLUXO_LIQUIDO_aux)

    #Exportar arrays calculados e atualizados
    return(arr_ADU, arr_TOG, arr_TOY, arr_TOR,
           arr_DEMANDA_QUALIFICADA, arr_ESTOQUE, arr_FLUXO_LIQUIDO,
           arr_PLANEJADO_PROJECAO,arr_planejado, arr_planejado_entrega)