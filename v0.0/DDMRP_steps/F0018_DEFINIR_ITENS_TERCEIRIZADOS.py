import pandas as pd
import numpy as np
import os

def def_definir_itens_com_tercerizacao(base_path, folder_name, file_name, df_parametros, df_estrutura, lista_materiais):

    """Adiciona ao arquivo de parametros a coluna TERC que indica se o item referente tem terceirização ou não.
    A tercerização é definida por se o item pai tem um filho no nível seguinte que esta na lista de itens tercerizados.
    
    Retorna o dataframe de parametros com a coluna TERC."""


    #Criar item linha tercerizado
    df_parametros["TERC"] = "NÃO"
    
    #Criar lista de itens tercerizados
    df_terc = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                            dtype={"Material": str})
    lista_terc = df_terc["Material"].unique().tolist()
    
    #Para cada linha de df_estrutura
    i = 0

    for index, row in df_estrutura.iterrows():
        
        j = 1
        
        #Se o item esta na lista de itens ZDD e ainda existem colunas a seguir
        if (row["Componente"] in lista_materiais) and (i + j < len(df_estrutura)-1):
        
            #Ler as informações da linha seguinte
            j = 1
            SUB_COMP = str(df_estrutura.iloc[i + j]["Componente"])
            SUB_NIVEL = int(df_estrutura.iloc[i + j]["Nível"])
        
            #Enquanto o nivel abaixo não for maior que o nivel principal
            #E ainda tiver linhas abaixo
            while (SUB_NIVEL > row["Nível"]) and ((i + j) < (len(df_estrutura)-1)):
                
                #Se o item de nivel igual a MAIN_NIVEL+1 e for tercerizado
                if (SUB_COMP in lista_terc) and (SUB_NIVEL == row["Nível"]+1):
                    
                    #Atribuir tercerizaçaõ ao item
                    df_parametros["TERC"] = np.where(df_parametros["Material"].eq(row["Componente"]), "SIM", df_parametros["TERC"])
                    break
            
                #Ler linha seguinte
                j = j + 1
                SUB_COMP = str(df_estrutura.iloc[i + j]["Componente"])
                SUB_NIVEL = int(df_estrutura.iloc[i + j]["Nível"])
        
        i = i + 1

    #Retornar dataframe de parametros com a coluna TERC adicionada
    return(df_parametros)