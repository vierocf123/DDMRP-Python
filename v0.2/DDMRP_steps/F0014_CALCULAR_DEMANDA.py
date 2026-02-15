import pandas as pd
import numpy as np
import os

def def_calcular_demanda(base_path, folder_name, file_name1, file_name2, lista_materiais, data_ref,
                         file_name_pop, lista_materiais_PMP):

    '''Lê relatório de carteira e estrutura e combina ambos para definir a demanda real
    para cada item, mantém apenas itens presentes lista_materiais.
    
    Retorna: dataframe de demanda para valor sem atraso, dataframe de demanda para valores em atraso,
    arquivo de estrutura*
    
    OBS: o arquivo de estrutura é exportado porque será usado posteriormente para identificar itens tercerizaveis.'''

    ########## CARTEIRA ##########

    #Ler dados de carteira
    df_carteira = pd.read_excel(os.path.join(base_path, folder_name, file_name1),
                                dtype={"Material": str,
                                       "Quantidade pendente": float})

    #Manter colunas de importantes
    colunas_interesse = ["Material","Data de remessa","Quantidade pendente"]
    df_carteira = df_carteira[[col for col in colunas_interesse if col in df_carteira.columns]]

    #Transformar "Data de remessa" em DateTime
    df_carteira["Data de remessa"] = pd.to_datetime(df_carteira["Data de remessa"], errors="coerce").dt.date

    #Filtrar carteira pela data de referencia
    df_carteira.loc[df_carteira["Data de remessa"] < data_ref, "Data de remessa"] = "ATRASO"

    #Agrupar demanda diaria do material
    df_carteira = (df_carteira
                   .groupby(["Material", "Data de remessa"], as_index=False)["Quantidade pendente"].sum())

    ########## ESTRUTURA ##########

    #Ler dados de estrutura
    df_estrutura = pd.read_excel(os.path.join(base_path, folder_name, file_name2),
                                 dtype={"Material": str,
                                        "Componente": str,
                                        "Nível": int,
                                        "Quantidade Unitária": float})

    #Armazenar estrutura para calcular tercerizados
    colunas_interesse = ["Material","Nível","Componente"]
    df_estrutura_terc = df_estrutura[[col for col in colunas_interesse if col in df_estrutura.columns]]
    
    #Manter colunas de importantes
    colunas_interesse = ["Material","Componente","Quantidade Unitária"]
    df_estrutura = df_estrutura[[col for col in colunas_interesse if col in df_estrutura.columns]]
    
    #Agrupar demanda do componente do material
    df_estrutura = (
        df_estrutura
        .groupby(["Material", "Componente"], as_index=False)["Quantidade Unitária"]
        .sum())
    
    #Adicionar o próprio Material a sua estrutura
    materiais_unicos = df_estrutura["Material"].drop_duplicates()
    df_complementar = pd.DataFrame({
        "Material": materiais_unicos,
        "Componente": materiais_unicos,
        "Quantidade Unitária": 1})
    df_estrutura = pd.concat([df_complementar, df_estrutura], ignore_index=True)

    ########### DEMANDA ###########

    #Unir dataframes de Estrutura e Demanda
    df_demanda = pd.merge(df_carteira, df_estrutura, on='Material', how='left')
    
    #Calcular demanda
    df_demanda["Demanda"] = (df_demanda["Quantidade Unitária"]*df_demanda["Quantidade pendente"]).fillna(0)

    #Remover colunas desnecessarias
    df_demanda = df_demanda[["Data de remessa", "Componente", "Demanda"]]

    #Agrupar demanda por data e componente
    df_demanda = (df_demanda
                  .groupby(["Data de remessa", "Componente"], as_index=False)["Demanda"]
                  .sum())
    
    #Remover componente não DDMRP (não presente em dado mestre)
    df_demanda = df_demanda.rename(columns={"Componente": "Material"})
    df_demanda = df_demanda[df_demanda["Material"].isin(lista_materiais)].copy()
    
    #Renomear colunas
    df_demanda = df_demanda.rename(columns={"Data de remessa": "DATA", "Demanda": "QTD"})

    ############# Adicionar Demanda POP ID ###############
    df_demanda_pop = pd.read_excel(os.path.join(base_path, folder_name, file_name_pop),
                                dtype={"Material": str,
                                       "Entrada/Necess.": float})
    #Manter colunas de importantes
    colunas_interesse = ["Material","Entrada/Necess.","Data rem./fim base"]
    df_demanda_pop = df_demanda_pop[[col for col in colunas_interesse if col in df_demanda_pop.columns]]

    #Transformar "Data de remessa" em DateTime
    df_demanda_pop["Data rem./fim base"] = pd.to_datetime(df_demanda_pop["Data rem./fim base"], errors="coerce").dt.date

    #Filtrar carteira pela data de referencia
    df_demanda_pop.loc[df_demanda_pop["Data rem./fim base"] < data_ref, "Data rem./fim base"] = "ATRASO"

    #Manter apenas itens PMP
    df_demanda_pop = df_demanda_pop[df_demanda_pop["Material"].isin(lista_materiais_PMP)]

    #Renomear colunas
    df_demanda_pop = df_demanda_pop.rename(columns={"Data rem./fim base": "DATA", "Entrada/Necess.": "QTD"})

    #Adicionar demanda do POP ao arquivo de demanda
    df_demanda = pd.concat([df_demanda, df_demanda_pop], ignore_index=True)

    #Agrupar demanda por data e material
    df_demanda = (df_demanda
                  .groupby(["DATA", "Material"], as_index=False)["QTD"]
                  .sum())
    
    #######################################################

    #Ajustar df_demanda_atraso
    df_demanda_atraso = df_demanda[df_demanda["DATA"] == "ATRASO"]
    df_demanda_atraso.drop(columns=["DATA"], inplace=True)
    df_demanda_atraso = df_demanda_atraso.rename(columns={"QTD": "ATRASO"})
    
    #Manter apenas itens sem atraso em df_demanda
    df_demanda = df_demanda[df_demanda["DATA"] != "ATRASO"]

    #Retornar Dataframes
    return(df_demanda, df_demanda_atraso, df_estrutura_terc)