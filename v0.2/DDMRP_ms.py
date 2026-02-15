print(r" ____  ____  __  __  ____   ____  ")
print(r"|  _ \|  _ \|  \/  |  __ \ |  __ \ ")
print(r"| | | | | | | \  / | |__) || |__) |")
print(r"| | | | | | | |\/| |  _  / |  __ /")
print(r"| |/ /| |/ /| |  | | | \ \ | |")
print(r"|___/ |___/ |_|  |_|_|  \_\|_|.py")

#Lendo bibliotecas, variaveis iniciais
print("Iniciando Execução --------------------------------------- 01/26")

"""Lendo bibliotecas e arquivos auxiliares .py"""

import pandas as pd
import numpy as np
import datetime as dt
import os
import time
import bisect
import warnings
from functools import reduce
from DDMRP_steps.F0001_INTERFACE_DDMRP import ler_parametros_gui, aviso_final
from DDMRP_steps.F0002_LER_DADOS_MESTRES import def_ler_dados_mestres
from DDMRP_steps.F0003_LER_DADOS_AJUSTE import def_ler_dados_de_ajuste
from DDMRP_steps.F0004_LER_PARAMETROS_DE_GRUPO import def_ler_parametros_de_grupo
from DDMRP_steps.F0005_LER_ESTOQUE import def_ler_estoque
from DDMRP_steps.F0006_LER_CUSTOS import def_ler_custo
from DDMRP_steps.F0007_LER_ORDENS_DE_PRODUCAO import def_ler_ops
from DDMRP_steps.F0008_LER_ORDENS_DE_COMPRA import def_ler_ocs
from DDMRP_steps.F0009_LER_NIPS import def_ler_nips
from DDMRP_steps.F0010_LER_RESERVAS import def_ler_reservas
from DDMRP_steps.F0011_LER_DAF import def_ler_DAF
from DDMRP_steps.F0012_LER_CALENDARIO import def_ler_calendario
from DDMRP_steps.F0013_LER_CONSUMO import def_ler_consumo
from DDMRP_steps.F0014_CALCULAR_DEMANDA import def_calcular_demanda
from DDMRP_steps.F0015_CALCULAR_DATA_REF import def_calcular_data
from DDMRP_steps.F0016_DEFINIR_PARAMETROS_DEFAULT import def_setar_parametros_default
from DDMRP_steps.F0017_AJUSTAR_PARAMETROS import def_ajustar_parametros_de_materiais
from DDMRP_steps.F0018_DEFINIR_ITENS_TERCEIRIZADOS import def_definir_itens_com_tercerizacao
from DDMRP_steps.F0019_VETORIZAR_DADOS import def_vetorizar_dados
from DDMRP_steps.F0020_CALCULAR_PLANEJADO import def_calcular_planejamento
from DDMRP_steps.F0021_CALCULAR_PROJECAO import def_calcular_projecao
from DDMRP_steps.F0022_EXPORTAR_RELATORIOS import def_exportar_vetor, def_exportar_consumo, def_exportar_demanda, def_exportar_dados_agrupados, def_exportar_projecao_SAP, exportar_projecao_PBI, def_exportar_planejado_SAP, def_exportar_planejado_PBI

#Iniciar execução
if __name__ == "__main__":

    #Ignorar avisos
    warnings.filterwarnings("ignore") 
    
    #Ler variaveis do usuário #############################################################################################
    print("Lendo Parâmetros do Usuário ------------------------------ 02/26")

    inputs_usuario = ler_parametros_gui()
    data_ref = dt.date(inputs_usuario['ano'], inputs_usuario['mes'], inputs_usuario['dia'])
    base_dir = inputs_usuario['pasta']
    del inputs_usuario #Liberar memória

    inicio = time.time() #Tempo de execução

    #Ler variaveis do usuário #############################################################################################
    print("Lendo Dados Mestres -------------------------------------- 03/26")

    df_dados_mestres = def_ler_dados_mestres(base_dir,
                                             r"0.Relatorios SAP",
                                             "cadastro.XLSX")
    
    #Ler variaveis do ajustes #############################################################################################
    print("Lendo Dados de Ajuste ------------------------------------ 04/26")

    df_ajuste, df_dados_mestres, lista_de_materiais, lista_materiais_DDMRP, lista_materiais_PMP = def_ler_dados_de_ajuste(base_dir,
                                                                                                                          r"5.Arquivos Manuais",
                                                                                                                          "ajustes.XLSX",
                                                                                                                          df_dados_mestres)

    #Ler arquivo de Parâmetros de Grupo ###################################################################################
    print("Lendo Parâmetros de Grupo -------------------------------- 05/26")
    
    df_parametros_de_grupo = def_ler_parametros_de_grupo(base_dir,
                                                         r"5.Arquivos Manuais",
                                                         "parametros_de_grupo.XLSX")

    #Ler arquivo de Estoque e Estoque Kanbam ##############################################################################
    print("Lendo Estoques ------------------------------------------- 06/26")

    df_estoque = def_ler_estoque(base_dir,
                                 r"0.Relatorios SAP",
                                 "estoque.XLSX",
                                 "kanban lift.XLSX",
                                 lista_de_materiais)

    #Ler arquivo de Custo #################################################################################################
    print("Lendo Custos --------------------------------------------- 07/26")

    df_custo = def_ler_custo(base_dir,
                             r"0.Relatorios SAP",
                             "custo.XLSX",
                             lista_de_materiais)

    #Ler arquivo de Ordens de Produção ####################################################################################
    print("Lendo Ordens de Produção --------------------------------- 08/26")

    df_ops, df_ops_saldo, df_ops_status, df_ops_totais = def_ler_ops(base_dir,
                                                                     r"0.Relatorios SAP",
                                                                     "ops.XLSX",
                                                                     lista_de_materiais,
                                                                     data_ref)

    #Ler arquivo de Ordens de Compra ######################################################################################
    print("Lendo Ordens de Compra ----------------------------------- 09/26")

    df_ocs, df_ocs_saldo, df_ocs_status, df_ocs_totais = def_ler_ocs(base_dir,
                                                                     r"0.Relatorios SAP",
                                                                     "ocs.XLSX",
                                                                     lista_de_materiais,
                                                                     df_dados_mestres["PlMRP"].unique(),
                                                                     data_ref)

    #Ler arquivo de NIPs ##################################################################################################
    print("Lendo NIPs ----------------------------------------------- 10/26")

    df_nips, df_nips_saldo, df_nips_status = def_ler_nips(base_dir,
                                                          r"0.Relatorios SAP",
                                                          "nips.XLSX",
                                                          lista_de_materiais,
                                                          data_ref)

    #Ler arquivo de Reservas ##############################################################################################
    print("Lendo Reservas ------------------------------------------- 11/26")

    df_reservas, df_reservas_saldo = def_ler_reservas(base_dir,
                                                      r"0.Relatorios SAP",
                                                      "reservas.XLSX",
                                                      lista_de_materiais,
                                                      data_ref)
    
    #Ler arquivo de DAF ###################################################################################################
    print("Lendo DAFs ----------------------------------------------- 12/26")
    
    df_DAF = def_ler_DAF(base_dir,
                         r"5.Arquivos Manuais",
                         "daf.XLSX",
                         lista_de_materiais,
                         data_ref)

    #Ler arquivo de Calendário ############################################################################################
    print("Lendo Dias Bloqueados ------------------------------------ 13/26")
    
    df_dias_bloqueados, lista_dias_bloqueados = def_ler_calendario(base_dir,
                                                                   r"5.Arquivos Manuais",
                                                                   "calendario.XLSX")

    #Ler arquivo de Consumo ###############################################################################################
    print("Lendo Consumo -------------------------------------------- 14/26")

    df_consumo = def_ler_consumo(base_dir,
                                 r"0.Relatorios SAP",
                                 "consumo.XLSX",
                                 lista_de_materiais,
                                 data_ref)

    #Calcular Demanda #####################################################################################################
    print("Calculando Demanda --------------------------------------- 15/26")

    df_demanda, df_demanda_ATRASO, df_estrutura = def_calcular_demanda(base_dir,
                                                                       r"0.Relatorios SAP",
                                                                       "demanda.xlsx",
                                                                       "estrutura.XLSX",
                                                                       lista_de_materiais,
                                                                       data_ref,
                                                                       "demanda_pmp.xlsx",
                                                                       lista_materiais_PMP)
    
    #Criar datas de referência ############################################################################################
    print("Calculando Datas de Referência --------------------------- 16/26")

    data_fluxo_semanal_i = def_calcular_data(data_ref=data_ref, datas_bloqueadas=lista_dias_bloqueados, dias_corridos=1)
    data_fluxo_semanal_f = def_calcular_data(data_ref=data_ref, datas_bloqueadas=lista_dias_bloqueados, dias_corridos=200)
    data_ref_consumo_i = def_calcular_data(data_ref=data_ref, datas_bloqueadas=lista_dias_bloqueados, dias_corridos=120, tipo=False)
    data_ref_carteira_f = def_calcular_data(data_ref=data_ref, datas_bloqueadas=lista_dias_bloqueados, dias_corridos=320)

    #Criar dados DDMRP default ############################################################################################
    print("Atribuindo Parâmetros Default ---------------------------- 17/26")

    df_parametros = def_setar_parametros_default(df_dados_mestres)

    #Criar dados DDMRP ajustado ############################################################################################
    print("Realizando Ajustes de Parâmetros ------------------------- 18/26")

    df_parametros = def_ajustar_parametros_de_materiais(df_parametros,
                                                        df_ajuste,
                                                        df_parametros_de_grupo,
                                                        lista_de_materiais)
    
    #Criar dados DDMRP ajustado ############################################################################################
    print("Identificando Itens com Terceirização -------------------- 19/26")

    df_parametros = def_definir_itens_com_tercerizacao(base_dir,
                                                       r"0.Relatorios SAP",
                                                       "tercerizados.xlsx",
                                                       df_parametros,
                                                       df_estrutura,
                                                       lista_de_materiais)

    #Vetorização dos dados ################################################################################################
    print("Vetorizando Dados Diários -------------------------------- 20/26")    

    arr_consumo_demanda, arr_OCs_OPs, arr_NIPs_completo, arr_reservas_completo, arr_DAF, df_demanda, df_consumo, arr_demanda = def_vetorizar_dados(lista_de_materiais, lista_dias_bloqueados,
                                                                                                                                                   df_demanda, data_ref_carteira_f,
                                                                                                                                                   df_consumo, data_ref_consumo_i,
                                                                                                                                                   df_ops, df_ocs, df_reservas, df_DAF, df_nips,
                                                                                                                                                   data_ref, data_fluxo_semanal_f)

    #Calcular projeção dos dados ##########################################################################################
    print("Calculando Planejado ------------------------------------- 21/26")

    df_parametros, arr_planejado, arr_planejado_entrega, lista_DDMRP_fluxo, lista_DDMRP_completo, lista_DDMRP_fluxo_DIAS, lista_DDMRP_completo_DIAS = def_calcular_planejamento(data_ref, data_ref_consumo_i, data_ref_carteira_f, lista_dias_bloqueados,
                                                                                                                                                                                data_fluxo_semanal_f, df_parametros, df_estoque, df_nips_saldo,
                                                                                                                                                                                arr_consumo_demanda, arr_DAF, arr_reservas_completo, lista_de_materiais,
                                                                                                                                                                                df_demanda_ATRASO)

    #Calcular projeção dos dados ##########################################################################################
    print("Calculando Projeção -------------------------------------- 22/26")

    arr_ADU, arr_TOG, arr_TOY, arr_TOR, arr_DEMANDA_QUALIFICADA, arr_ESTOQUE, arr_FLUXO_LIQUIDO, arr_PLANEJADO_PROJECAO,arr_planejado, arr_planejado_entrega = def_calcular_projecao(data_ref,
                                                                                                                                                                                     lista_DDMRP_completo, lista_DDMRP_completo_DIAS,
                                                                                                                                                                                     lista_DDMRP_fluxo, lista_DDMRP_fluxo_DIAS,
                                                                                                                                                                                     df_parametros,
                                                                                                                                                                                     arr_planejado_entrega,
                                                                                                                                                                                     arr_consumo_demanda,
                                                                                                                                                                                     arr_NIPs_completo,
                                                                                                                                                                                     arr_planejado,
                                                                                                                                                                                     arr_DAF,
                                                                                                                                                                                     arr_demanda)
  
    #Exportar Dados ##########################################################################################
    print("Exportando Vetores --------------------------------------- 23/26")
    
    #Exportar vetores em D0
    def_exportar_vetor(arr_TOG, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "TOG.xlsx", "D0")
    def_exportar_vetor(arr_TOY, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "TOY.xlsx", "D0")
    def_exportar_vetor(arr_TOR, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "TOR.xlsx", "D0")
    def_exportar_vetor(arr_ADU, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "ADU.xlsx", "D0")
    def_exportar_vetor(arr_DEMANDA_QUALIFICADA, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "DEMANDA_QUALIFICADA.xlsx", "D0")
    def_exportar_vetor(arr_ESTOQUE, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "ESTOQUE.xlsx", "D0")
    def_exportar_vetor(arr_FLUXO_LIQUIDO, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "FLUXO_LIQUIDO.xlsx", "D0")
    def_exportar_vetor(arr_DAF, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "DAF.xlsx", "D0")
    def_exportar_vetor(arr_planejado, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "planejado.xlsx", "D0")
    def_exportar_vetor(arr_planejado_entrega, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "planejado_entrega.xlsx", "D0")

    #Exportar vetores com ATRASO
    def_exportar_vetor(arr_reservas_completo, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "reservas.xlsx", "ATRASO")
    def_exportar_vetor(arr_OCs_OPs, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "OCs_OPs.xlsx", "ATRASO")
    def_exportar_vetor(arr_NIPs_completo, lista_DDMRP_fluxo, lista_de_materiais, base_dir, r"4.Relatorios Python", "nips_tempo.xlsx", "ATRASO")

    #Exportar Consumo e Demanda
    def_exportar_consumo(df_consumo, data_ref, base_dir, r"4.Relatorios Python", "CONSUMO.xlsx")
    def_exportar_demanda(df_demanda, df_demanda_ATRASO, data_fluxo_semanal_f, base_dir, r"4.Relatorios Python", "demanda.xlsx")

    print("Exportando Relatórios Complementares --------------------- 24/26")

    #Exportar informações pontuais
    def_exportar_dados_agrupados(df_ops_saldo, base_dir, r"4.Relatorios Python", "ops_saldos.xlsx")
    def_exportar_dados_agrupados(df_ops_totais, base_dir, r"4.Relatorios Python", "ops_totais.xlsx")
    def_exportar_dados_agrupados(df_ops_status, base_dir, r"4.Relatorios Python", "ops_atraso_andamento.xlsx")
    def_exportar_dados_agrupados(df_ocs_totais, base_dir, r"4.Relatorios Python", "ocs_total.xlsx")
    def_exportar_dados_agrupados(df_ocs_status, base_dir, r"4.Relatorios Python", "ocs_atraso_andamento.xlsx")
    def_exportar_dados_agrupados(df_ocs_saldo, base_dir, r"4.Relatorios Python", "ocs_saldos.xlsx")
    def_exportar_dados_agrupados(df_reservas_saldo, base_dir, r"4.Relatorios Python", "reservas_saldo.xlsx")
    def_exportar_dados_agrupados(df_ajuste, base_dir, r"4.Relatorios Python", "ajuste.xlsx")
    def_exportar_dados_agrupados(df_parametros, base_dir, r"4.Relatorios Python", "parametros.xlsx")
    def_exportar_dados_agrupados(df_nips_saldo, base_dir, r"4.Relatorios Python", "nips_saldo.xlsx")
    def_exportar_dados_agrupados(df_nips_status, base_dir, r"4.Relatorios Python", "NIP_andamento.xlsx")

    print("Exportando Relatórios para Power BI ---------------------- 25/26")

    #Exportar Bases para PowerBI
    exportar_projecao_PBI(lista_DDMRP_fluxo,
                          lista_de_materiais,
                          data_ref, df_parametros,
                          df_custo,
                          base_dir, r"3.Projeção",
                          arr_TOG, arr_TOY, arr_TOR, arr_ADU, arr_ESTOQUE, arr_FLUXO_LIQUIDO, arr_planejado, arr_planejado_entrega, arr_DAF, arr_NIPs_completo)
    
    def_exportar_planejado_PBI(df_dados_mestres, df_custo, df_parametros,
                               df_ops_totais, df_ops_saldo, df_ops_status,
                               df_ocs_totais, df_ocs_saldo, df_ocs_status,
                               lista_de_materiais, data_ref, base_dir, r"2.Historico")

    print("Exportando Relatórios para SAP --------------------------- 26/26")

    #Exportar Relatórios SAP
    def_exportar_projecao_SAP(arr_PLANEJADO_PROJECAO,
                              lista_DDMRP_fluxo,
                              lista_de_materiais,
                              df_dados_mestres, base_dir, "1.Cargas SAP",
                              data_ref,
                              df_parametros)
    
    def_exportar_planejado_SAP(df_parametros, df_dados_mestres, base_dir, "1.Cargas SAP", data_ref)

    #Concluir Execução ####################################################################################################
    fim = time.time()
    tempo_final = (fim-inicio)/60
    print(f"Fim da Execução! Tempo de Execução: {tempo_final:.2f} minutos.")
    aviso_final()