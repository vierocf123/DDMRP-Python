import pandas as pd
import numpy as np
import os

def def_ler_ocs(base_path, folder_name, file_name, lista_materiais, planejadores_DDMRP, data_ref):

    """Lê ordens de compra, mantém apenas itens presentes em lista materiais, define o tipo de ordem baseado
    na lista de PLANEJADORES dos itens DDMRP, cria e retorna a visualização de ops em quatro formas:
    1. SALDO de OCs ao longo do tempo;
    2. SALDO de OCs agrupados por tipo de ordem;
    3. SALDO de OCs agrupados por status (ATRASO/ANDAMENTO);
    4. TOTAL de OCs agrupados por tipo de ordem"""

    #Ler dados de OCs
    df_ocs = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                        engine="openpyxl",
                        dtype={"Material": str})
    
    #Transformar "Data de remessa" em DateTime
    df_ocs["Rem/FimBas"] = pd.to_datetime(df_ocs["Rem/FimBas"], errors="coerce").dt.date
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "Entrada/Nec.",
                        "Rem/FimBas",
                        "PlMRP"]
    df_ocs = df_ocs[[col for col in colunas_interesse if col in df_ocs.columns]]
    
    #Remover materiais não necessarios
    df_ocs = df_ocs[df_ocs["Material"].isin(lista_materiais)].copy()

    #Criar Lista de OCs DD e não DD
    df_ocs["TIPO"] = np.where(df_ocs["PlMRP"].isin(planejadores_DDMRP), "DD", "NAO_DD")
    
    #Separar por DD e NAO_DD
    df_ocs_saldos = (df_ocs[["Material", "Entrada/Nec.", "TIPO"]]
                     .pivot_table(
                         index="Material",
                         columns="TIPO",
                         values="Entrada/Nec.",
                         aggfunc="sum",   # soma caso haja duplicados
                         fill_value=0)
                         .reindex(columns=["DD", "NAO_DD"], fill_value=0)
                         .reset_index())
    df_ocs_saldos.columns.name = None

    #Separar por DD e NAO_DD
    df_ocs_TOTAL = (df_ocs.groupby(["Material", "TIPO"])
                    .size()
                    .unstack(fill_value=0)       # vira colunas A/B
                    .reindex(columns=["DD", "NAO_DD"], fill_value=0)  # garante ordem/colunas
                    .reset_index())

    #Ajustar data de OCs
    df_ocs.loc[df_ocs["Rem/FimBas"] < data_ref, "Rem/FimBas"] = "ATRASO"
    
    #Agrupar OCs
    df_ocs = (
        df_ocs
        .groupby(["Material", "Rem/FimBas"], as_index=False)["Entrada/Nec."]
        .sum())

    #Criar OCs por categoria
    df_ocs_atraso_andamento = df_ocs
    df_ocs_atraso_andamento.loc[df_ocs_atraso_andamento["Rem/FimBas"] != "ATRASO", "Rem/FimBas"] = "ANDAMENTO"
    
    #Criar agrupamento
    df_ocs_atraso_andamento = (df_ocs_atraso_andamento.groupby(["Material", "Rem/FimBas"])
                            .size()
                            .unstack(fill_value=0)       # vira colunas A/B
                            .reindex(columns=["ATRASO","ANDAMENTO"], fill_value=0)  # garante ordem/colunas
                            .reset_index())
    df_ocs_atraso_andamento = df_ocs_atraso_andamento.reset_index(drop=True)

    #Retornar dataframes
    return(df_ocs, df_ocs_saldos, df_ocs_atraso_andamento, df_ocs_TOTAL)