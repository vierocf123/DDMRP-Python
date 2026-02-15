import pandas as pd
import numpy as np
import os

def def_setar_parametros_default(dados_mestres):

    """Calcula apartir do dataframe do dado mestre os parametros dafault dos materiais:
    categorização do tipo de material, tempo de consumo (30), tempo de demanda (30), tipo de dias utilizado,
    seta ADU móvel para todos os itens.
    
    Retorna: dataframe de parametros com informações geradas e demais atributos utilizados nas próximas etapas."""

    #Construir dados mestres apenas com colunas necessarias para o DDMRP
    df_parametros = dados_mestres[["Material",
                                    "Denominação",
                                    "TMat",
                                    "TipSupr.",
                                    "TEM",
                                    "PEP",
                                    "TamMínLote",
                                    "ValArredond."]]
    
    #Atribuir TIPO_MATERIAL a df_parametros
    df_parametros["TIPO_MATERIAL"] = np.select(
        [
            df_parametros["TMat"].isin(["ZFE1", "ZFE2"]),
            (df_parametros["TMat"].isin(["ZHA1", "ZHA2"])) & (df_parametros["TipSupr."] == "F"),
            df_parametros["TMat"].isin(["ZHA1", "ZHA2"]),
            df_parametros["TMat"].isin(["ZHI", "ZHI1"]),
            df_parametros["TMat"].isin(["ZRO1", "ZRO2", "ZUN1"])
        ],
        [
            "PRODUTO-PRONTO",
            "TERCERIZADO",
            "MANUFATURADO",
            "CONSUMIVEL",
            "MATERIA-PRIMA"
        ],
        default=None)
    
    #Atribuir valore Default
    mask_corrido = df_parametros["TIPO_MATERIAL"].isin(["MATERIA-PRIMA", "CONSUMIVEL", "TERCERIZADO"])
    mask_util    = df_parametros["TIPO_MATERIAL"].isin(["PRODUTO-PRONTO", "MANUFATURADO"])
    
    #Remover None
    df_parametros = df_parametros[df_parametros["TIPO_MATERIAL"].notna()]

    #Inicializa as colunas (opcional, mas ajuda a manter ordem e tipo)
    for col in ["DIAS_CONSUMO", "DIAS_DEMANDA", "TIPO_DIA"]:
        if col not in df_parametros.columns:
            df_parametros[col] = np.nan

    #Categorias que usam "CORRIDO"
    df_parametros.loc[mask_corrido, ["DIAS_CONSUMO", "DIAS_DEMANDA"]] = 30
    df_parametros.loc[mask_corrido, "TIPO_DIA"] = "CORRIDO"
    
    #Categorias que usam "UTIL"
    df_parametros.loc[mask_util, ["DIAS_CONSUMO", "DIAS_DEMANDA"]] = 30
    df_parametros.loc[mask_util, "TIPO_DIA"] = "UTIL"
    
    #ADU FIXA sempre "N"
    df_parametros["ADU_FIXA"] = "N"

    #Atribuir DIAS_DE_ANTECIPACAO default
    df_parametros["DIAS_DE_ANTECIPACAO"] = int(0)

    #Retornar dataframe de parametros
    return(df_parametros)