import pandas as pd
import numpy as np
import datetime as dt
import os

def def_vetorizar_dados(lista_materiais, datas_bloqueadas,
                        df_demanda, data_f_demanda,
                        df_consumo, data_i_consumo,
                        df_ops, df_ocs, df_reservas, df_daf, df_nips,
                        data_ref, data_f_projecao):

    """ Transforma os dados em vetores para otimizar a busca e calculo de informações.
    Delimita os ranges de valores baseado em datas. Preenche datas vazias com 0 e insere todos os materiais
    de lista_materiais.
    
    Retora: dados vetorizados"""

    ###### CARTEIRA ######

    """ Delimita os dados de carteira pela data_ref e data_f_demanda, removendo valores fora do range. """

    #Cria o range de datas
    datas = pd.date_range(start=data_ref, end=data_f_demanda, freq="D").date

    #Cria grid de Material x Data
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "DATA"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_demanda_completo = (df_grid.merge(df_demanda, on=["Material", "DATA"], how="left").fillna({"QTD": 0}))
    
    #Garante que QTD é numérico
    df_demanda_completo["QTD"] = df_demanda_completo["QTD"].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_demanda_completo = df_demanda_completo[~df_demanda_completo["DATA"].isin(datas_bloqueadas)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_demanda_completo = df_demanda_completo.sort_values(by=['Material', 'DATA'])

    #Exportar range de demanda completo com array
    arr_demanda = df_demanda_completo.pivot(index=['Material'], columns='DATA', values='QTD')
    arr_demanda = arr_demanda.sort_values(by=['Material'])
    arr_demanda = arr_demanda.rename_axis(columns=None).reset_index()
    arr_demanda = arr_demanda.drop(columns=["Material"]).to_numpy()    
    
    ###### CONSUMO ######
    
    """ Delimita os dados de consumo pela data_i_consumo e a data_ref, removendo valores fora do range."""

    #Cria o range de datas
    datas = pd.date_range(start=data_i_consumo, end=(data_ref - dt.timedelta(days=1)), freq="D").date
    
    #Cria grid de Material x Data
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "DATA"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_consumo_completo = (df_grid.merge(df_consumo, on=["Material", "DATA"], how="left").fillna({"QTD": 0}))
    
    #Garante que QTD é numérico
    df_consumo_completo["QTD"] = df_consumo_completo["QTD"].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_consumo_completo = df_consumo_completo[~df_consumo_completo["DATA"].isin(datas_bloqueadas)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_consumo_completo = df_consumo_completo.sort_values(by=['Material', 'DATA'])
    
    ###### CONSUMO E DEMANDA ######

    """ Combina os dataframes de demanda e consumo para vetoriza-los. """

    #Criar demanda completa
    df_consumo_demanda = pd.concat([df_consumo_completo, df_demanda_completo], ignore_index=True)
    df_consumo_demanda = df_consumo_demanda.sort_values(by=['Material', 'DATA'])
    
    #Pivot df_consumo_demanda
    df_consumo_demanda = df_consumo_demanda.pivot(index=['Material'], columns='DATA', values='QTD')
    df_consumo_demanda = df_consumo_demanda.sort_values(by=['Material'])
    df_consumo_demanda = df_consumo_demanda.rename_axis(columns=None).reset_index()
    
    #Transformar df_consumo_demanda em array
    arr_consumo_demanda = df_consumo_demanda.drop(columns=["Material"]).to_numpy()

    ###### RESERVA ######

    """ Delimita os dados de reservas pela data_ref e data_f_projecao, removendo valores maiores que o range
    e categorizando valores menores como ATRASO"""

    #Cria o range de datas
    datas = pd.date_range(start=data_ref, end=data_f_projecao, freq="D").date
    datas = ["ATRASO"] + list(datas)
    
    #Cria grid de Material x Data
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "Rem/FimBas"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_reservas_completo = (df_grid.merge(df_reservas, on=["Material", "Rem/FimBas"], how="left").fillna({"Entrada/Nec.": 0}))
    
    #Garante que QTD é numérico
    df_reservas_completo["Entrada/Nec."] = df_reservas_completo["Entrada/Nec."].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_reservas_completo = df_reservas_completo[~df_reservas_completo["Rem/FimBas"].isin(datas_bloqueadas)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_reservas_completo = df_reservas_completo.sort_values(by=['Material', 'Rem/FimBas'])
    
    #Pivot df_reservas_completo
    df_reservas_completo = df_reservas_completo.pivot(index=['Material'], columns='Rem/FimBas', values='Entrada/Nec.')
    
    #Se não existir, cria a coluna ATRASO com zeros
    if "ATRASO" not in df_reservas_completo.columns:
        df_reservas_completo["ATRASO"] = 0
    
    #Reordena colunas colocando ATRASO na segunda posição
    cols = list(df_reservas_completo.columns)
    cols.insert(0, cols.pop(cols.index("ATRASO")))
    df_reservas_completo = df_reservas_completo[cols]
    df_reservas_completo = df_reservas_completo.sort_values(by=['Material'])
    df_reservas_completo = df_reservas_completo.rename_axis(columns=None).reset_index()
    
    #Transformar df_reservas_completo em array
    arr_reservas_completo = df_reservas_completo.drop(columns=["Material"]).to_numpy()

    ###### NIPs #######

    """ Delimita os dados de NIPs pela data_ref e data_f_projecao, removendo valores maiores que o range
    e categorizando valores menores como ATRASO"""

    #Cria o range de datas
    datas = pd.date_range(start=data_ref, end=data_f_projecao, freq="D").date
    datas = ["ATRASO"] + list(datas)

    #Cria grid de Material x Data
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "Rem/FimBas"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_NIPs_completo = (df_grid.merge(df_nips, on=["Material", "Rem/FimBas"], how="left").fillna({"Qtd.plan.": 0}))
    
    #Garante que QTD é numérico
    df_NIPs_completo["Qtd.plan."] = df_NIPs_completo["Qtd.plan."].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_NIPs_completo = df_NIPs_completo[~df_NIPs_completo["Rem/FimBas"].isin(datas_bloqueadas)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_NIPs_completo = df_NIPs_completo.sort_values(by=['Material', 'Rem/FimBas'])
    
    #Pivot df_NIPs_completo
    df_NIPs_completo = df_NIPs_completo.pivot(index=['Material'], columns='Rem/FimBas', values='Qtd.plan.')
    
    #Se não existir, cria a coluna ATRASO com zeros
    if "ATRASO" not in df_NIPs_completo.columns:
        df_NIPs_completo["ATRASO"] = 0
    
    #Reordena colunas colocando ATRASO na segunda posição
    cols = list(df_NIPs_completo.columns)
    cols.insert(0, cols.pop(cols.index("ATRASO")))
    df_NIPs_completo = df_NIPs_completo[cols]
    df_NIPs_completo = df_NIPs_completo.sort_values(by=['Material'])
    df_NIPs_completo = df_NIPs_completo.rename_axis(columns=None).reset_index()

    #Transformar df_reservas_completo em array
    arr_NIPs_completo = df_NIPs_completo.drop(columns=["Material"]).to_numpy()

    ###### OCs e OPs #######
    
    """ Combina os dados de saldo de OCs e OPs e delimita os pela data_ref e data_f_projecao,
    removendo valores maiores que o range e categorizando valores menores como ATRASO"""

    #Renomear colunas dos dataframes
    df_ocs = df_ocs.rename(columns={"Rem/FimBas": "Data",
                                    "Entrada/Nec.": "Qtd"})
    df_ops = df_ops.rename(columns={"Data de conclusão base": "Data",
                                    "SALDO": "Qtd"})
    #Combinar dataframes de OCs e OPs
    df_ops_ocs = pd.concat([df_ops, df_ocs], ignore_index=True)
    
    #Agrupa por Material e Data
    df_ops_ocs = (df_ops_ocs
                .groupby(["Material", "Data"], as_index=False)["Qtd"]
                .sum())
    
    #Cria o range de datas
    datas = pd.date_range(start=data_ref, end=data_f_projecao, freq="D").date
    datas = ["ATRASO"] + list(datas)
    
    #Cria grid de Material x Data
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "Data"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_OCs_OPs = (df_grid.merge(df_ops_ocs, on=["Material", "Data"], how="left").fillna({"Qtd": 0}))
    
    #Garante que QTD é numérico
    df_OCs_OPs["Qtd"] = df_OCs_OPs["Qtd"].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_OCs_OPs = df_OCs_OPs[~df_OCs_OPs["Data"].isin(datas_bloqueadas)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_OCs_OPs = df_OCs_OPs.sort_values(by=['Material', 'Data'])
    
    #Pivot df_OCs_OPs
    df_OCs_OPs = df_OCs_OPs.pivot(index=['Material'], columns='Data', values='Qtd')
    
    #Se não existir, cria a coluna ATRASO com zeros
    if "ATRASO" not in df_OCs_OPs.columns:
        df_OCs_OPs["ATRASO"] = 0
    
    #Reordena colunas colocando ATRASO na segunda posição
    cols = list(df_OCs_OPs.columns)
    cols.insert(0, cols.pop(cols.index("ATRASO")))
    df_OCs_OPs = df_OCs_OPs[cols]
    df_OCs_OPs = df_OCs_OPs.sort_values(by=['Material'])
    df_OCs_OPs = df_OCs_OPs.rename_axis(columns=None).reset_index()
    
    #Transformar df_reservas_completo em array
    arr_OCs_OPs = df_OCs_OPs.drop(columns=["Material"]).to_numpy()

    ###### DAF ######
    
    """ Expande os valores do relatorio de DAF para todas as datas do intervalo. Delimita os pela data_ref e 
    data_f_projecao, removendo valores fora do range."""

    #Criar DAF expandido
    df_DAF_completo = df_daf.rename(columns={"CÓDIGO": "Material"})
    df_DAF_completo["_datas"] = [
        pd.date_range(s, e, freq="D", inclusive="left") if pd.notna(s) and pd.notna(e) else pd.DatetimeIndex([])
        for s, e in zip(df_DAF_completo["DT.INÍCIO"], df_DAF_completo["DT.FIM"])]
    df_DAF_completo = (
        df_DAF_completo[["Material", "_datas", "%"]]
        .explode("_datas", ignore_index=True)
        .rename(columns={"_datas": "Data"}))
    df_DAF_completo["Data"] = pd.to_datetime(df_DAF_completo["Data"], errors="coerce") #!
    df_DAF_completo["Data"] = df_DAF_completo["Data"].dt.date
    df_DAF_completo = df_DAF_completo.drop_duplicates(subset=["Material", "Data"])
    df_DAF_completo = df_DAF_completo[df_DAF_completo["Data"] >= data_ref]
    
    #Cria o range de datas
    datas = pd.date_range(start=data_ref, end=data_f_projecao, freq="D").date
    
    #Cria grid de Material x Data
    grid = pd.MultiIndex.from_product([lista_materiais, datas], names=["Material", "Data"])
    df_grid = pd.DataFrame(index=grid).reset_index()
    
    #Junta com o dataframe original
    df_DAF_completo = (df_grid.merge(df_DAF_completo, on=["Material", "Data"], how="left").fillna({"%": 1}))
    
    #Garante que QTD é numérico
    df_DAF_completo["%"] = df_DAF_completo["%"].astype(float)
    
    #Remover linhas cujas datas estão no calendário (DIAS BLOQUEADOS)
    df_DAF_completo = df_DAF_completo[~df_DAF_completo["Data"].isin(datas_bloqueadas)].reset_index(drop=True)
    
    #Ordenar dataframe por Material e Data
    df_DAF_completo = df_DAF_completo.sort_values(by=['Material', 'Data'])
    
    #Pivot df_consumo_demanda
    df_DAF_completo = df_DAF_completo.pivot(index=['Material'], columns='Data', values='%')
    df_DAF_completo = df_DAF_completo.sort_values(by=['Material'])
    df_DAF_completo = df_DAF_completo.rename_axis(columns=None).reset_index()

    #Transformar df_DAF_completo em array
    arr_DAF = df_DAF_completo.drop(columns=["Material"]).to_numpy()

    #Retornar vetorizações
    return(arr_consumo_demanda, arr_OCs_OPs, arr_NIPs_completo, arr_reservas_completo, arr_DAF, df_demanda_completo, df_consumo_completo, arr_demanda)
