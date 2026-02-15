import pandas as pd
import numpy as np
import os

def def_ler_nips(base_path, folder_name, file_name, lista_materiais, data_ref):

    """Lê NIPs, mantém apenas itens presentes em lista materiais,
    cria e retorna a visualização de ops em quatro formas:
    1. SALDO de NIPs ao longo do tempo;
    2. SALDO de NIPs total;
    3. SALDO de NIPs agrupados por status (ATRASO/ANDAMENTO)."""

    #Ler dados de NIPs
    df_nips = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                            engine="openpyxl",
                            dtype={"Material": str})
    
    #Transformar "Data de remessa" em DateTime
    df_nips["Rem/FimBas"] = pd.to_datetime(df_nips["Rem/FimBas"], errors="coerce").dt.date
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "Qtd.plan.",
                        "Rem/FimBas"]
    df_nips = df_nips[[col for col in colunas_interesse if col in df_nips.columns]]
    
    #Remover nips não necessarios
    df_nips = df_nips[df_nips["Material"].isin(lista_materiais)].copy()
    df_nips = df_nips[df_nips["Qtd.plan."] > 0]

    #Ajustar data de NIPs
    df_nips.loc[df_nips["Rem/FimBas"] < data_ref, "Rem/FimBas"] = "ATRASO"
    
    #Agrupar NIPs
    df_nips = (
        df_nips
        .groupby(["Material", "Rem/FimBas"], as_index=False)["Qtd.plan."]
        .sum())

    #Definir nips pelo status de entrega (atraso/em andamento)
    df_NIPS_entrega = df_nips.copy()
    df_NIPS_entrega.loc[df_NIPS_entrega["Rem/FimBas"] != "ATRASO", "Rem/FimBas"] = "EM ANDAMENTO"
    df_NIPS_entrega = df_NIPS_entrega.groupby(['Material', 'Rem/FimBas'])['Qtd.plan.'].sum()
    df_NIPS_entrega = df_NIPS_entrega.reset_index()
    df_NIPS_entrega = df_NIPS_entrega.pivot(index='Material', columns='Rem/FimBas', values='Qtd.plan.')
    df_NIPS_entrega = df_NIPS_entrega.fillna(0)
    df_NIPS_entrega = df_NIPS_entrega.reset_index()

    #Agrupar NIPs
    df_nips_SALDO = (
        df_nips
        .groupby(["Material"], as_index=False)["Qtd.plan."]
        .sum())
    
    #Retornar dataframes
    return(df_nips, df_nips_SALDO, df_NIPS_entrega)