import pandas as pd
import numpy as np
import os

def def_ajustar_parametros_de_materiais(df_parametros, df_ajuste, df_parametros_de_grupo, lista_materiais):

    """Integra os parametros SAP com os parametros imputados pelo usuário sobrepondo as informações do SAP
    com as informações manuais inseridas. Calcula o LT e o fator de LT.
    
    Retorna: dataframe de parametros do material"""

    ###### ARQUIVO DE AJUSTE ######

    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "LT FAB",
                        "LT NEST",
                        "LT TERC",
                        "Ciclo DDMRP",
                        "CICLO DESEJ.",
                        "HORIZ. PICO ORDEM",
                        "DIAS CONSUMO",
                        "DIAS DEMANDA",
                        "TIPO DE DIAS",
                        "ADU FIXA",
                        "HORIZONTE FIXO",
                        "DIAS DE ANTECIPAÇÃO",
                        "CALCULAR ITEM",
                        "LT PMP"]
    df_ajuste = df_ajuste[[col for col in colunas_interesse if col in df_ajuste.columns]]

    #Ajustar erros de código
    df_ajuste.loc[df_ajuste["ADU FIXA"] != "S", "ADU FIXA"] = "N"
    
    #Renomear colunas
    df_ajuste = df_ajuste.rename(columns={"DIAS CONSUMO": "DIAS_CONSUMO",
                                          "DIAS DEMANDA": "DIAS_DEMANDA",
                                          "TIPO DE DIAS": "TIPO_DIA",
                                          "ADU FIXA": "ADU_FIXA",
                                          "DIAS DE ANTECIPAÇÃO": "DIAS_DE_ANTECIPACAO",
                                          "CALCULAR ITEM": "TIPO_PLANEJAMENTO"})
    
    #Filtrar Ajuste apenas com IDs que existem em DadoMestre
    df_ajuste = df_ajuste[df_ajuste["Material"].isin(lista_materiais)].copy()   

    ###### UNIR DF_AJUSTE E DF_PARAMETROS ######

    #Fundir dataframes
    df_parametros = pd.merge(df_parametros, df_ajuste, on="Material", how="outer", suffixes=("_df1", "_df2"))

    #Combinar dataframes
    df_parametros["DIAS_CONSUMO"] = df_parametros["DIAS_CONSUMO_df2"].combine_first(df_parametros["DIAS_CONSUMO_df1"])
    df_parametros["DIAS_DEMANDA"] = df_parametros["DIAS_DEMANDA_df2"].combine_first(df_parametros["DIAS_DEMANDA_df1"])
    df_parametros["TIPO_DIA"] = df_parametros["TIPO_DIA_df2"].combine_first(df_parametros["TIPO_DIA_df1"])
    df_parametros["ADU_FIXA"] = df_parametros["ADU_FIXA_df2"].combine_first(df_parametros["ADU_FIXA_df1"])
    df_parametros["DIAS_DE_ANTECIPACAO"] = df_parametros["DIAS_DE_ANTECIPACAO_df2"].combine_first(df_parametros["DIAS_DE_ANTECIPACAO_df1"])

    #Remove as colunas duplicadas
    df_parametros = df_parametros.drop(columns=["DIAS_CONSUMO_df2", "DIAS_CONSUMO_df1", "DIAS_DEMANDA_df2", "DIAS_DEMANDA_df1",
                                                "TIPO_DIA_df2", "TIPO_DIA_df1", "ADU_FIXA_df2", "ADU_FIXA_df1",
                                                "DIAS_DE_ANTECIPACAO_df1", "DIAS_DE_ANTECIPACAO_df2"])

    #Aplicar Ajustes aos valores
    df_parametros["LT FAB"] = df_parametros["LT FAB"].fillna(0)
    df_parametros["LT NEST"] = df_parametros["LT NEST"].fillna(0)
    df_parametros["LT TERC"] = df_parametros["LT TERC"].fillna(0)
    df_parametros["Ciclo DDMRP"] = df_parametros["Ciclo DDMRP"].fillna(0)

    #Calcular DLT
    df_parametros["DLT"] = np.where(df_parametros["TIPO_PLANEJAMENTO"] == "DDMRP",
                                    df_parametros["LT FAB"] + df_parametros["LT NEST"] + df_parametros["LT TERC"] + df_parametros["TEM"] + df_parametros["PEP"] + df_parametros["Ciclo DDMRP"],
                                    df_parametros["LT PMP"])
    df_parametros['DLT'] = df_parametros['DLT'].fillna(0)

    ###### PARAMETROS DE GRUPO ######

    #Inserir parametros de grupo
    df_parametros = pd.merge(df_parametros, df_parametros_de_grupo, on=['Denominação', 'TIPO_MATERIAL'], how='left')

    #Definir parametro de DLT
    condicoes = [
        (df_parametros["DLT"] == 0),
        (df_parametros['DLT'] <= df_parametros["DLT LIM INF"]),
        (df_parametros['DLT'] <= df_parametros["DLT LIM SUP"]),
        (df_parametros['DLT'] > df_parametros["DLT LIM SUP"])]
    escolhas = [df_parametros["DLT M"], df_parametros["DLT S"], df_parametros["DLT M"], df_parametros["DLT L"]]
    df_parametros['FATOR DLT'] = np.select(condicoes, escolhas)
    escolhas = ["M","S","M","L"]
    df_parametros['LMS'] = np.select(condicoes, escolhas)

    #Remover colunas desnecessarias
    df_parametros = df_parametros.drop(columns=["DLT S", "DLT M", "DLT L","DLT LIM INF","DLT LIM SUP"])

    #Retornar dataframe
    return(df_parametros)