import pandas as pd
import numpy as np
import os

def def_ler_parametros_de_grupo(base_path, folder_name, file_name):

    """Lê parametros de grupo para itens DDMRP
    
    retorna: dataframe de parametros de grupo."""

    #Ler dados de parametros de grupo
    df_parametros_de_grupo = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                                        engine="openpyxl",
                                        dtype={"UNIDADE": str,
                                                "TIPO_MATERIAL": str,
                                                "VAR LIM INF": float, "VAR LIM SUP": float,
                                                "VAR L": float, "VAR M": float, "VAR H": float,
                                                "DLT LIM INF": float, "DLT LIM SUP": float,
                                                "DLT S": float, "DLT M": float, "DLT L": float,})
    #Remonear colunas
    df_parametros_de_grupo = df_parametros_de_grupo.rename(columns={'UNIDADE': 'Denominação'})

    #Retornar dataframe de parametros de grupo
    return(df_parametros_de_grupo)