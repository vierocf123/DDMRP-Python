import pandas as pd
import numpy as np
import os

def def_ler_dados_de_ajuste(base_path, folder_name, file_name, df_dado_mestre):

    """Lê arquivo de ajuste criado pelo usuário, remove itens duplicados, 
    filtra apenas itens que terão o DDMRP calculado. Filtra o arquivo de dados mestres e
    cria lista ordenada de todos os itens DDMRP.
    
    Retorna: Dataframe de Ajuste, Dataframe de Dados Mestre filtrado, lista ordenada de itens DDMRP."""

    #Ler arquivo de AJUSTE
    df_AJUSTE = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                        engine="openpyxl",
                        dtype={"MATERIAL": str})
    
    #Remover dados duplicados
    df_AJUSTE = df_AJUSTE.drop_duplicates(subset=['MATERIAL'], keep="first")
    
    #Filtrar df_AJUSTE para apenas itens "DDMRP"
    df_AJUSTE = df_AJUSTE[df_AJUSTE["CALCULAR ITEM"] == "DDMRP"].copy()

    #Definir itens que possuem ambos os fatores SAP e Manuais
    lista_materiais_DDMRP = set(df_AJUSTE["MATERIAL"]) & set(df_dado_mestre["Material"])

    #Remover itens de lista_materiais_DDMRP que não estão em df_dado_mestre
    df_AJUSTE = df_AJUSTE[df_AJUSTE['MATERIAL'].isin(lista_materiais_DDMRP)]
    
    #Remover itens de df_dado_mestre que não estão em lista_materiais_DDMRP
    df_dado_mestre = df_dado_mestre[df_dado_mestre['Material'].isin(lista_materiais_DDMRP)]

    #Ordenar lista_materiais_DDMRP
    lista_materiais_DDMRP = list(lista_materiais_DDMRP)
    lista_materiais_DDMRP = sorted(lista_materiais_DDMRP)

    #Renomear colunas
    df_AJUSTE = df_AJUSTE.rename(columns={'MATERIAL': 'Material'})

    #Retornar variáveis
    return(df_AJUSTE, df_dado_mestre, lista_materiais_DDMRP)