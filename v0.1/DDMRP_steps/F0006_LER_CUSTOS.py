import pandas as pd
import numpy as np
import os

def def_ler_custo(base_path, folder_name, file_name, lista_materiais):

    """Lê arquivo de custos SAP, calcula custo baseado na regra (preço standard / por),
    mantém apenas itens presentes em lista_materiais."""

    #Ler dados de custo
    df_custo = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                                engine="openpyxl",
                                dtype={"Material": str})
    
    #Calcular custo
    df_custo["CUSTO"] = df_custo["Prç.standard"]/df_custo["por"]
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "CUSTO"]
    
    df_custo = df_custo[[col for col in colunas_interesse if col in df_custo.columns]]
    
    #Remover custos não necessarios
    df_custo = df_custo[df_custo["Material"].isin(lista_materiais)].copy()
    
    #Remover Duplicados
    df_custo = df_custo.drop_duplicates(subset=['Material'], keep="first")

    #Retornar dataframe de custos
    return(df_custo)