import pandas as pd
import numpy as np
import os

def def_ler_estoque(base_path, folder_name, file_name1, file_name2, lista_materiais):

    """Lê arquivo de estoque;
    Remove colunas desnecessárias, estoque em terceiro e materiais que não estão em lista_materiais
    Calcula SALDO = UTILIZAÇÃO LIVRE + CONTROLE DE QUALIDADE + EM TRANSPORTE
    Agrupa valores por material e integra com o estoque Kanbam"""

    #Ler dados de estoque
    df_estoque = pd.read_excel(os.path.join(base_path, folder_name, file_name1),
                               engine="openpyxl",
                               dtype={"Material": str})

    #Remover Estoque em Terceiro
    df_estoque = df_estoque[df_estoque['Depósito'].notna()]
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "Utilização livre",
                        "Trânsito e TE",
                        "Controle qualidade",
                        "Depósito."]
    df_estoque = df_estoque[[col for col in colunas_interesse if col in df_estoque.columns]]

    #Calcular valor de estoque
    df_estoque["SALDO"] = df_estoque["Utilização livre"]+df_estoque["Trânsito e TE"]+df_estoque["Controle qualidade"]

    #Agrupar por material
    df_estoque = df_estoque.groupby("Material", as_index=False)["SALDO"].sum()

    #Remover estoques não necessarios
    df_estoque = df_estoque[df_estoque["Material"].isin(lista_materiais)].copy()

    #Ler dados de estoque Kanban
    df_estoque_kb = pd.read_excel(os.path.join(base_path, folder_name, file_name2),
                                engine="openpyxl",
                                dtype={"Material": str})
    
    #Ajustar variaveis
    df_estoque_kb["Material"] = df_estoque_kb["Material"].astype(str)  # garante que é string
    df_estoque_kb["Material"] = df_estoque_kb["Material"].apply(lambda x: x.zfill(18) if x.isdigit() else x)
    df_estoque_kb = df_estoque_kb.groupby("Material", as_index=False)["Qtd.Kanban"].sum()

    #Adicionar informação ao df_estoque_kb
    df_estoque = pd.merge(df_estoque, df_estoque_kb, on='Material', how='left')
    df_estoque['Qtd.Kanban'].fillna(0, inplace = True)

    #Ajustar saldo
    df_estoque["SALDO"] = df_estoque["SALDO"] - df_estoque["Qtd.Kanban"]
    df_estoque["ERRO_NO_LIFT"] = np.where(df_estoque["SALDO"] < 0, "ERRO", "")
    df_estoque["SALDO"] = (df_estoque["SALDO"]).clip(lower=0)

    #Retornar dataframe de estoque
    return(df_estoque)