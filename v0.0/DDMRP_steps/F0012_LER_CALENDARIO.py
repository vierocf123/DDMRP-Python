import pandas as pd
import numpy as np
import os

def def_ler_calendario(base_path, folder_name, file_name):

    """Lê arquivo manual de calendario e ordena por ordem crescente.
    
    Retoro: dataframe de dias bloqueados e lista de dias bloqueados"""

    #Ler arquivo de calendario
    df_calendario = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                        engine="openpyxl")
    
    #Ajustar datas
    df_calendario["DIAS BLOQUEADOS"] = pd.to_datetime(df_calendario["DIAS BLOQUEADOS"], errors="coerce").dt.date

    #Gerar lista de dias bloqueados
    lista_dias_bloqueados = df_calendario["DIAS BLOQUEADOS"].dropna().tolist()

    #Ordenar dataframe e lista
    df_calendario = df_calendario.sort_values(by='DIAS BLOQUEADOS')
    lista_dias_bloqueados = sorted(lista_dias_bloqueados)
    
    #Retornar dataframe
    return(df_calendario, lista_dias_bloqueados)