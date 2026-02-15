import pandas as pd
import numpy as np
import os

def def_ler_reservas(base_path, folder_name, file_name, lista_materiais, data_ref):

    """Lê reservas, mantém apenas itens presentes em lista_materiais,
    cria e retorna a visualização de reservas em duas formas:
    1. SALDO de reservas ao longo do tempo;
    2. SALDO de reservas total."""

    #Ler dados de Reservas
    df_reservas = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                                engine="openpyxl",
                                dtype={"Material": str})
    
    #Transformar "Data de remessa" em DateTime
    df_reservas["Rem/FimBas"] = pd.to_datetime(df_reservas["Rem/FimBas"], errors="coerce").dt.date
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "Entrada/Nec.",
                        "Rem/FimBas"]
    df_reservas = df_reservas[[col for col in colunas_interesse if col in df_reservas.columns]]
    
    #Remover reservas não necessarios
    df_reservas = df_reservas[df_reservas["Material"].isin(lista_materiais)].copy()
    df_reservas = df_reservas[df_reservas["Entrada/Nec."] > 0]
    
    #Ajustar data de reservas
    df_reservas.loc[df_reservas["Rem/FimBas"] < data_ref, "Rem/FimBas"] = "ATRASO"
    
    #Agrupar Reservas
    df_reservas = (
        df_reservas
        .groupby(["Material","Rem/FimBas"], as_index=False)["Entrada/Nec."]
        .sum())

    #Agrupar Reservas
    df_reservas_SALDO = (
        df_reservas
        .groupby(["Material"], as_index=False)["Entrada/Nec."]
        .sum())
    
    #Retornar dataframes
    return(df_reservas, df_reservas_SALDO)