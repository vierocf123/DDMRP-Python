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
                          arr_planejado_entrega, arr_consumo_demanda, arr_NIPs, arr_planejado, arr_DAF, arr_demanda):

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
        if tamanho_lote_min <= 0:
            tamanho_lote_min = int(1)
        tamanho_lote_mult = float(row["ValArredond."])        
        if tamanho_lote_mult <= 0:
            tamanho_lote_mult = int(1)
        ciclo_desejado = float(row["CICLO DESEJ."])
        TOG = float(row["TOG"])
        TOY = float(row["TOY"])
        TOR = float(row["TOR"])
        R1 = float(row["R1"])
        tipo_de_planejamento = str(row["TIPO_PLANEJAMENTO"])
        qtd_atraso = float(row["CARTEIRA_EM_ATRASO"])
        dias_periodo_firme = int(row["DLT"])
        dias_antecipacao = int(row["DIAS_DE_ANTECIPACAO"])

        #Escolher modulo de planejamento conforme tipo_de_planejamento
        if tipo_de_planejamento == "PMP":

            ########################################################################################################
            ### PMP ################################################################################################
            ########################################################################################################

            demanda_atraso = qtd_atraso
            demanda_qualificada_atraso = demanda_atraso

            #Calcular Demanda Qualificada [deslocamento da demanda dado o periodo firme]
            if dias_antecipacao > 0:
                
                #Loop contador de dias
                i = 0
                arr_DEMANDA_QUALIFICADA_aux += [0] * len(lista_DDMRP_fluxo)

                #Para cada dia lista_DDMRP_fluxo
                for data_ref_fluxo in lista_DDMRP_fluxo:

                    #Calcular passos para antecipacao
                    antecipacao_i, antecipacao_f = calcular_range(v_dias_uteis=lista_DDMRP_fluxo_DIAS,
                                                                  datas=lista_DDMRP_fluxo,
                                                                  data=data_ref_fluxo,
                                                                  tipo="UTIL",
                                                                  dias=dias_antecipacao,
                                                                  sentido=False,
                                                                  excludente=True)
                    
                    #Se o item entrou na zona de atraso [não cumpriu o tempo necessario de antecipacao]
                    if np.sum(lista_DDMRP_fluxo_DIAS[antecipacao_f:antecipacao_i+1]) < dias_antecipacao:

                        #Atribuir demanda para o atraso
                        demanda_qualificada_atraso = demanda_qualificada_atraso + arr_demanda[index][i]

                    #Antecipar o item
                    else:

                        #Adicionar a antecipação da demanda no dia especifico
                        arr_DEMANDA_QUALIFICADA_aux[antecipacao_f] = arr_demanda[index][i]

                    i = i + 1

            #Caso o item haja antecipacao
            else:

                #Se não houver antecipacao, a demanda qualificada é igual a demanda
                arr_DEMANDA_QUALIFICADA_aux = arr_demanda[index][:201]
            
            #Armazenar demanda em atraso ajustada
            df_parametros.loc[index,"QTD_ATRASO_ADJ"] = demanda_atraso

            #Definir informações sobre o range de periodo firme e primeira data em aberto
            periodo_firme_i, periodo_firme_f = calcular_range(v_dias_uteis=lista_DDMRP_fluxo_DIAS,
                                                            datas=lista_DDMRP_fluxo,
                                                            data=data_ref,
                                                            tipo=tipo_dia,
                                                            dias=dias_periodo_firme,
                                                            sentido=True,
                                                            excludente=False)
            
            data_pf = lista_DDMRP_fluxo[periodo_firme_f]

            #Saldo de backlog [NIP ATRASO + ESTOQUE + DEMANDA EM ATRASO]
            saldo = np.sum(arr_NIPs[index][:1]) + float(row["ESTOQUE"]) - demanda_qualificada_atraso
            estoque = float(row["ESTOQUE"]) - demanda_atraso + np.sum(arr_NIPs[index][:1])

            #Parametros de loop
            i = 0

            #Para cada data dentro do periodo firme
            for data_ref_fluxo in lista_DDMRP_fluxo[:periodo_firme_f+1]:

                #Definir saldo dos dias em periodo firme
                saldo = saldo + np.sum(arr_NIPs[index][i+1]) - np.sum(arr_DEMANDA_QUALIFICADA_aux[i])
                estoque = estoque + np.sum(arr_NIPs[index][i+1]) - np.sum(arr_demanda[index][i])

                #Armazenar estoque e fluxo liquido e
                arr_ADU_aux.append(None)
                arr_TOG_aux.append(None)
                arr_TOY_aux.append(None)
                arr_TOR_aux.append(None)
                arr_ESTOQUE_aux.append(estoque)
                arr_FLUXO_LIQUIDO_aux.append(saldo)
                
                i = i + 1

            limite_pf = i
            producao_fim_pf_d1 = 0

            #Para cada data em fora do periodo firme
            for data_ref_fluxo in lista_DDMRP_fluxo[periodo_firme_f+1:]:

                #Atualizar Saldo (NIPs de HOJE - DEMANDAS de HOJE)
                saldo = saldo + np.sum(arr_NIPs[index][i+1]) - np.sum(arr_DEMANDA_QUALIFICADA_aux[i])

                #Se o Saldo for negativo
                if saldo < 0:

                    #Calcular NIP com base no lote minimo
                    NIP = np.ceil(abs(saldo)/tamanho_lote_mult)*tamanho_lote_mult

                    #Definir data de entrega e inicio de producao
                    producao_i, producao_f = calcular_range(v_dias_uteis=lista_DDMRP_fluxo_DIAS,
                                                            datas=lista_DDMRP_fluxo,
                                                            data=data_ref_fluxo,
                                                            tipo="UTIL",
                                                            dias=dlt,
                                                            sentido=False,
                                                            excludente=False)
                    
                    indice_entrega = producao_i
                    indice_producao = producao_f
                    
                    #Se a data de produção infrigir o Periodo Firme
                    if producao_f <= periodo_firme_f:

                        #Recalcular Data de Entrega de Produção
                        indice_producao = periodo_firme_f + 1

                        producao_i, producao_f = calcular_range(v_dias_uteis=lista_DDMRP_fluxo_DIAS,
                                                                datas=lista_DDMRP_fluxo,
                                                                data=lista_DDMRP_fluxo[indice_producao],
                                                                tipo=tipo_dia,
                                                                dias=dlt,
                                                                sentido=True,
                                                                excludente=False)
                        
                        indice_entrega = producao_f
                        indice_producao = producao_i

                    #Armazenar Entrega e Inicio
                    arr_planejado[index][indice_producao] = arr_planejado[index][indice_producao] + NIP
                    arr_planejado_entrega[index][indice_entrega] = arr_planejado_entrega[index][indice_entrega] + NIP

                    #Armazenar Data de entrega da primeira data fora do Periodo Firme
                    if limite_pf == i:
                        producao_fim_pf_d1 = producao_f
                    
                    #Caso contrario armazenar entrega na projecao
                    else:
                        arr_PLANEJADO_PROJECAO[index][indice_entrega] = arr_PLANEJADO_PROJECAO[index][indice_entrega] + NIP

                #Caso contrario
                else:

                    NIP = 0

                #Atualizar Saldo e Estoque
                saldo = saldo + NIP
                estoque = estoque + np.sum(arr_NIPs[index][i+1]) + np.sum(arr_planejado_entrega[index][i]) - np.sum(arr_demanda[index][i])

                #Adicionar informações
                arr_ADU_aux.append(None)
                arr_TOG_aux.append(None)
                arr_TOY_aux.append(None)
                arr_TOR_aux.append(None)
                arr_ESTOQUE_aux.append(estoque)
                arr_FLUXO_LIQUIDO_aux.append(saldo)
                    
                i = i + 1

            #Atribuir NIP de planejamento
            df_parametros.loc[index,"DEMANDA_PF_D1"] = demanda_atraso + np.sum(arr_DEMANDA_QUALIFICADA_aux[:periodo_firme_f + 2])
            df_parametros.loc[index,"NIP_SUGERIDA"] = arr_planejado[index][periodo_firme_f + 1]
            if arr_planejado[index][periodo_firme_f+1] > 0:
                df_parametros.loc[index,"DATA_ENTREGA"] = lista_DDMRP_fluxo[producao_fim_pf_d1]
            df_parametros.loc[index,"FLUXO_LIQUIDO"] = arr_FLUXO_LIQUIDO_aux[periodo_firme_f + 1] - arr_planejado[index][periodo_firme_f + 1]
            if (df_parametros.loc[index, "DEMANDA_PF_D1"] == 0):
                df_parametros.loc[index, "PRIORIDADE%"] = 1
            else:
                df_parametros.loc[index, "PRIORIDADE%"] = ((df_parametros.loc[index, "FLUXO_LIQUIDO"] + df_parametros.loc[index, "DEMANDA_PF_D1"]) / df_parametros.loc[index, "DEMANDA_PF_D1"])

        elif tipo_de_planejamento == "DDMRP":

            ########################################################################################################
            ### DDMRP ##############################################################################################
            ########################################################################################################

            #Parametros de loop
            i = 0            
            
            #Estoque = Estoque - Demanda Hoje + NIPs Hoje + NIPs Atraso
            estoque = float(row["ESTOQUE"]) - (arr_consumo_demanda[index][indice]) + np.sum((arr_NIPs[index][0]))
            
            #NIP_ACUMULADA = Todas as NIPs + Planejado Hoje - Entrega Hoje - Entrega Atraso
            NIP_ACUMULADA = float(row["NIPs"]) + arr_planejado[index][0] - np.sum((arr_NIPs[index][0]))
            
            #Para cada data em lista_DDMRP_fluxo
            for data_ref_fluxo in lista_DDMRP_fluxo:
                
                #Se for a primeira Data:
                if i == 0:

                    #Adicionar parametros de planejamento do DDMRP
                    arr_ADU_aux.append(adu)
                    arr_TOG_aux.append(TOG)
                    arr_TOY_aux.append(TOY)
                    arr_TOR_aux.append(TOR)
                    arr_DEMANDA_QUALIFICADA_aux.append(0)
                    arr_ESTOQUE_aux.append(float(row["ESTOQUE"]))
                    arr_FLUXO_LIQUIDO_aux.append(float(row["FLUXO_LIQUIDO"]))

                #Se for outra data do fluxo
                else:

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