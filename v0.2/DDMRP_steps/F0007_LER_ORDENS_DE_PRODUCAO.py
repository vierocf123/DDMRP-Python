import pandas as pd
import numpy as np
import os

def def_ler_ops(base_path, folder_name, file_name, lista_materiais, data_ref):

    """Lê ordens de produção, calculo do saldo (quantidade da ordem - refugo - fornecida),
    mantém apenas itens presentes em lista materiais, cria e retorna a visualização de ops em quatro formas:
    1. SALDO de OPs ao longo do tempo;
    2. SALDO de OPs agrupados por tipo de ordem;
    3. SALDO de OPs agrupados por status (ATRASO/ANDAMENTO);
    4. TOTAL de OPs agrupados oir tipo de ordem"""

    #Ler dados de OPs
    df_ops = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                        engine="openpyxl",
                        dtype={"Material": str})
    
    #Transformar "Data de conclusão base" em DateTime
    df_ops["Data de conclusão base"] = pd.to_datetime(df_ops["Data de conclusão base"], errors="coerce").dt.date
    
    #Calcular saldo
    df_ops["SALDO"] = df_ops["Quantidade da ordem"]-df_ops["Quantidade de refugo confirmada"]-df_ops["Qtd.fornecida"]
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "SALDO",
                        "Data de conclusão base",
                        "Tipo de ordem"]
    df_ops = df_ops[[col for col in colunas_interesse if col in df_ops.columns]]
    
    #Remover materiais não necessarios
    df_ops = df_ops[df_ops["Material"].isin(lista_materiais)].copy()

    #Criar dataframe de saldos
    df_ops_saldos = df_ops.pivot_table(index="Material", 
                                       columns="Tipo de ordem",
                                       values="SALDO", 
                                       aggfunc="sum", 
                                       fill_value=0).reset_index()
    df_ops_saldos.columns.name = None

    #Criar saldo DDMRP e saldo não DDMRP
    cols_dd = [c for c in df_ops_saldos.columns if "DD" in c and c != "ID"]
    cols_not_dd = [c for c in df_ops_saldos.columns if "DD" not in c and c != "Material"]
    
    # Criar colunas de soma
    df_ops_saldos["SALDO_DD"] = df_ops_saldos[cols_dd].sum(axis=1)
    df_ops_saldos["SALDO_N_DD"] = df_ops_saldos[cols_not_dd].sum(axis=1)

    #Criar dataframe de totais
    df_ops_totais = pd.crosstab(df_ops["Material"], df_ops["Tipo de ordem"]).reset_index()
    df_ops_totais.columns.name = None
    
    #Criar total de ordens DDMRP e total não DDMRP
    cols_dd = [c for c in df_ops_totais.columns if "DD" in c and c != "ID"]
    cols_not_dd = [c for c in df_ops_totais.columns if "DD" not in c and c != "Material"]
    
    # Criar colunas de total
    df_ops_totais["TOTAL_DD"] = df_ops_totais[cols_dd].sum(axis=1)
    df_ops_totais["TOTAL_N_DD"] = df_ops_totais[cols_not_dd].sum(axis=1)
    
    #Criar as colunas pelo tipo da ordem
    for p in ["ZPD", "ZPK", "ZPP", "ZPR", "ZPS", "ZPT"]:
        cols = [c for c in df_ops_totais.columns if c.startswith(p)]
        df_ops_totais[p] = (df_ops_totais[cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                if cols else 0)
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "ZPD",
                        "ZPK",
                        "ZPP",
                        "ZPR",
                        "ZPS",
                        "ZPT",
                        "TOTAL_DD",
                        "TOTAL_N_DD"]
    df_ops_totais = df_ops_totais[[col for col in colunas_interesse if col in df_ops_totais.columns]]

    #Ajustar data de OPs
    df_ops.loc[df_ops["Data de conclusão base"] < data_ref, "Data de conclusão base"] = "ATRASO"
    
    #Agrupar OPs
    df_ops = (
        df_ops
        .groupby(["Material", "Data de conclusão base"], as_index=False)["SALDO"]
        .sum())

    #Criar OPs por categoria
    df_ops_atraso_andamento = df_ops
    df_ops_atraso_andamento.loc[df_ops_atraso_andamento["Data de conclusão base"] != "ATRASO", "Data de conclusão base"] = "ANDAMENTO"
    
    #Criar agrupamento
    df_ops_atraso_andamento = (df_ops_atraso_andamento.groupby(["Material", "Data de conclusão base"])
                            .size()
                            .unstack(fill_value=0)       # vira colunas A/B
                            .reindex(columns=["ATRASO","ANDAMENTO"], fill_value=0)  # garante ordem/colunas
                            .reset_index())
    df_ops_atraso_andamento = df_ops_atraso_andamento.reset_index(drop=True)

    #Retornar dataframes de ordens agrupadas:
    return(df_ops, df_ops_saldos, df_ops_atraso_andamento, df_ops_totais)