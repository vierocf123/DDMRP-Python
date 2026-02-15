import pandas as pd
import numpy as np
import os

def def_ler_DAF(base_path, folder_name, file_name, lista_materiais, data_ref):

    """Lê arquivo manual de DAFs, mantém apenas itens presentes em lista_materiais,
    remove DAFs experidas (DT.FIM < data_ref).
    
    Retoro: dataframe de DAFs com (MATERIAL, DT.INICIO, DT.FIM e %)"""

    #Ler arquivo de DAF
    df_DAF = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                        engine="openpyxl",
                        dtype={"CÓDIGO": str})
    #Ajustar datas
    df_DAF["DT.INÍCIO"] = pd.to_datetime(df_DAF["DT.INÍCIO"], errors="coerce").dt.date
    df_DAF["DT.FIM"] = pd.to_datetime(df_DAF["DT.FIM"], errors="coerce").dt.date

    #Remover materiais não necessarios
    df_DAF = df_DAF[df_DAF["CÓDIGO"].isin(lista_materiais)].copy()

    #Retornar dataframe
    return(df_DAF)