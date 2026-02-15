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
    
    #Filtrar df_AJUSTE para apenas itens "S"
    df_AJUSTE = df_AJUSTE[df_AJUSTE['CALCULAR ITEM'].isin(['DDMRP', 'PMP'])]

    #Listar itens sem DLT
    materiais_sem_LT_SAP_DDMRP = df_dado_mestre.loc[(df_dado_mestre['TEM'] == 0) & (df_dado_mestre['PEP'] == 0) & (df_dado_mestre['PlMRP'] == 505), 'Material'].tolist()
    materiais_sem_LT_AJUSTE_PMP = df_AJUSTE.loc[(df_AJUSTE['LT PMP'] == 0) & (df_AJUSTE['CALCULAR ITEM'] == "PMP"), 'MATERIAL'].tolist()
    materiais_sem_LT_AJUSTE_DDMRP = df_AJUSTE.loc[(df_AJUSTE['LT FAB'] == 0) &
                                                  (df_AJUSTE['LT NEST'] == 0) &
                                                  (df_AJUSTE['LT TERC'] == 0) & 
                                                  (df_AJUSTE['Ciclo DDMRP'] == 0) &
                                                  (df_AJUSTE['CALCULAR ITEM'] == "DDMRP"), 'MATERIAL'].tolist()
    materiais_sem_LT = (set(materiais_sem_LT_SAP_DDMRP) & set(materiais_sem_LT_AJUSTE_DDMRP)) | set(materiais_sem_LT_AJUSTE_PMP)
    materiais_sem_LT = list(materiais_sem_LT)

    #Definir itens que possuem ambos os fatores SAP e Manuais e possuem LT
    lista_materiais = (set(df_AJUSTE[df_AJUSTE["CALCULAR ITEM"].isin(["DDMRP", "PMP"])]["MATERIAL"]) & set(df_dado_mestre["Material"])) - set(materiais_sem_LT)

    #Remover itens de lista_materiais_DDMRP que não estão em df_dado_mestre
    df_AJUSTE = df_AJUSTE[df_AJUSTE['MATERIAL'].isin(lista_materiais)]
    
    #Remover itens de df_dado_mestre que não estão em lista_materiais_DDMRP
    df_dado_mestre = df_dado_mestre[df_dado_mestre['Material'].isin(lista_materiais)]

    #Ordenar lista_materiais_DDMRP
    lista_materiais = list(lista_materiais)
    lista_materiais = sorted(lista_materiais)

    #Criar lista de materiais DDMRP e PMP
    lista_materiais_DDMRP = df_AJUSTE.loc[df_AJUSTE["CALCULAR ITEM"] == "DDMRP", "MATERIAL"].tolist()
    lista_materiais_PMP = df_AJUSTE.loc[df_AJUSTE["CALCULAR ITEM"] == "PMP", "MATERIAL"].tolist()

    #Renomear colunas
    df_AJUSTE = df_AJUSTE.rename(columns={'MATERIAL': 'Material'})

    #Retornar variáveis
    return(df_AJUSTE, df_dado_mestre, lista_materiais, lista_materiais_DDMRP, lista_materiais_PMP)