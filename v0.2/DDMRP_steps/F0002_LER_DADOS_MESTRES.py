import pandas as pd
import numpy as np
import os

def def_ler_dados_mestres(base_path, folder_name, file_name):

    """Lê o dado mestre, mantém colunas de interesse e remove duplicados.
    
    Retorna: dataframe de DadoMestre"""

    #Ler dados mestres
    df_dado_mestre = pd.read_excel(os.path.join(base_path, folder_name, file_name),
                                engine="openpyxl",
                                dtype={"Material": str})
    
    #Manter colunas de importantes
    colunas_interesse = ["Material",
                        "Texto breve de material",
                        "Denominação",
                        "Família",
                        "DenomIndStand.",
                        "RCtrP",
                        "TMat",
                        "PlMRP",
                        "TpM",
                        "TEM",
                        "PEP",
                        "Per.seg.",
                        "CódMargSeg",
                        "TL",
                        "Cal",
                        "Estq.segurança",
                        "Pt.reabast.",
                        "TamMínLote",
                        "Tam.máx.lote",
                        "Tam.fx.lote",
                        "ValArredond.",
                        "PerfCP",
                        "UMB",
                        "TipSupr."]
    
    df_dado_mestre = df_dado_mestre[[col for col in colunas_interesse if col in df_dado_mestre.columns]]
    
    #Remover dados duplicados
    df_dado_mestre = df_dado_mestre.drop_duplicates(keep="first")

    #Retornar dado mestre
    return(df_dado_mestre)