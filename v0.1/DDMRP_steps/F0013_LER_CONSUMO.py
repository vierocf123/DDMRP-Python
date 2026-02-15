import pandas as pd
import numpy as np
import os

def def_ler_consumo(base_path, folder_name, file_name, lista_materiais, data_ref):

    """Lê relatório de consumo de material, mentém registros de interesse (material presente
    na lista_materiais e de data de entrada menor que data_ref). Agrupa valores por data de entrada
    
    Retorna: dataframe de consumo."""

    #Ler dados de consumo
    df_consumo = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                               engine="openpyxl",
                               dtype={"Material": str,
                                      "Qtd.  UM registro": float})
    
    #Remover materiais não DDMRP (não presente em dado mestre)
    df_consumo = df_consumo[df_consumo["Material"].isin(lista_materiais)].copy()
    
    #Manter colunas de importantes
    colunas_interesse = ["Material","Data de entrada","Qtd.  UM registro"]
    df_consumo = df_consumo[[col for col in colunas_interesse if col in df_consumo.columns]]
    
    #Transformar "Data de remessa" em DateTime
    df_consumo["Data de entrada"] = pd.to_datetime(df_consumo["Data de entrada"], errors="coerce").dt.date
    
    #Filtrar consumo pela data de referencia
    df_consumo = df_consumo[df_consumo["Data de entrada"] < data_ref]
    
    #Transformar registro para valores positivos
    df_consumo["Qtd.  UM registro"] = abs(df_consumo["Qtd.  UM registro"])
    
    #Agrupar demanda diaria do material
    df_consumo = (
        df_consumo
        .groupby(["Material", "Data de entrada"], as_index=False)["Qtd.  UM registro"]
        .sum())
    
    #Renomear colunas
    df_consumo = df_consumo.rename(columns={"Data de entrada": "DATA", "Qtd.  UM registro": "QTD"})

    #Retornar dataframe de consumo
    return(df_consumo)