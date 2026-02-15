import pandas as pd
import numpy as np
import datetime as dt
from functools import reduce
import os

def def_exportar_vetor(vetor, datas_projecao, lista_materiais, base_dir, folder, filename, tipo):
    
    """Exporta vetores de dados gerados para excel, converte vetor em dataframe e adiciona materiais
    e datas no cabeçalho das colunas"""

    #Definir range de datas
    if tipo == "D1":
        datas_projecao = datas_projecao[1:]
    elif tipo ==  "ATRASO":
        datas_projecao = ['ATRASO'] + datas_projecao

    #Transforma vetor de dataframe
    df = pd.DataFrame(vetor, columns=datas_projecao, index=lista_materiais)
    
    #Adicionar Materiais no inicio adiciona a coluna Material no início
    df.insert(0, "Material", lista_materiais)
    
    #Ordenar dataframe por material
    df = df.sort_values(by=['Material'])
    
    #Exportar arquivo
    caminho_completo = os.path.join(base_dir, folder, filename)
    df.to_excel(caminho_completo, index=False)


def def_exportar_consumo(df_consumo, data_ref, base_dir, folder, filename):

    """Exporta o relatório de consumo com os dados pivotados por data."""

    #Exportar consumo do fluxo semanal
    df_consumo_fluxo = df_consumo[df_consumo['DATA'] < data_ref]
    df_consumo_fluxo = df_consumo_fluxo.sort_values(by=['Material', 'DATA'])
    
    #Pivot df_consumo_demanda
    df_consumo_fluxo = df_consumo_fluxo.pivot(index=['Material'], columns='DATA', values='QTD')
    
    #Ordenar dataframe por material
    df_consumo_fluxo = df_consumo_fluxo.sort_values(by=['Material'])
    df_consumo_fluxo = df_consumo_fluxo.rename_axis(columns=None).reset_index()
    
    #Exportar arquivo
    caminho_completo = os.path.join(base_dir, folder, filename)
    df_consumo_fluxo.to_excel(caminho_completo, index=False)


def def_exportar_demanda(df_demanda_futura, df_demanda_atraso, data_f, base_dir, folder, filename):

    """Exporta os dados demanda de forma pivotada pelas datas, insere os valores em atraso na
    coluna ATRASO no inicio do dataframe."""

    #Exportar demanda do fluxo semanal
    df_demanda_fluxo_semanal = df_demanda_futura[df_demanda_futura['DATA'] <= data_f]
    df_demanda_fluxo_semanal = df_demanda_fluxo_semanal.sort_values(by=['Material', 'DATA'])
    
    #Pivot df_consumo_demanda
    df_demanda_fluxo_semanal = df_demanda_fluxo_semanal.pivot(index=['Material'], columns='DATA', values='QTD')
    
    #Inserir valores de demanda para atraso
    df_demanda_fluxo_semanal = df_demanda_fluxo_semanal.merge(df_demanda_atraso, on="Material", how="left")
    df_demanda_fluxo_semanal["ATRASO"] = df_demanda_fluxo_semanal["ATRASO"].fillna(0)
    df_demanda_fluxo_semanal.insert(1, "ATRASO", df_demanda_fluxo_semanal.pop("ATRASO"))
    
    #Ordenar dataframe por material
    df_demanda_fluxo_semanal = df_demanda_fluxo_semanal.sort_values(by=['Material'])
    
    #Exportar arquivo
    caminho_completo = os.path.join(base_dir, folder, filename)
    df_demanda_fluxo_semanal.to_excel(caminho_completo, index=False)


def def_exportar_dados_agrupados(df, base_dir, folder, filename):

    """Ordena o dataframe peleo código do material em ordem alfabética. Utilizado para exportar
    todos os relatórios que não estão pivotados por data."""

    #Ordenar dataframe por Material
    df = df.sort_values(by=['Material'])
    
    #Exportar arquivo
    caminho_completo = os.path.join(base_dir, folder, filename)
    df.to_excel(caminho_completo, index=False)


def def_exportar_projecao_SAP(arr_PLANEJADO_PROJECAO, datas_projecao, lista_materiais, df_dado_mestre, base_dir, folder, data_ref):

    """Exporta o relatório de projeção em .txt para ser utilizado no SAP, integra informações
    do dado mestre (UMB) e formata datas para serm lidas pelo SAP."""

    df_projecao_planejado = pd.DataFrame(arr_PLANEJADO_PROJECAO, columns=datas_projecao, index=lista_materiais)
    df_projecao_planejado.insert(0, "Material", lista_materiais)

    #Despivotar dados
    df_projecao_planejado = pd.melt(
        df_projecao_planejado,
        id_vars=df_projecao_planejado.columns[0],
        value_vars=df_projecao_planejado.columns[1:],
        var_name="DATA",
        value_name="QUANTITY")
    
    #Criar coluna Tipo
    df_projecao_planejado["TIPO"] = 1
    
    #Remover Quantidade Vazia
    df_projecao_planejado = df_projecao_planejado[df_projecao_planejado["QUANTITY"] > 0]
    
    #Inserir Unidade do Item
    df_projecao_planejado["UOM"] = df_projecao_planejado["Material"].map(df_dado_mestre.set_index("Material")["UMB"])
    
    #Ordenar dataframe
    df_projecao_planejado = df_projecao_planejado[["Material", "TIPO", "DATA", "QUANTITY", "UOM"]]
    df_projecao_planejado = df_projecao_planejado.rename(columns={"Material": "MATERIAL"})
    
    #Formater Variaveis
    df_projecao_planejado["DATA"] = (pd.to_datetime(df_projecao_planejado['DATA'], errors='coerce').dt.strftime('%d.%m.%Y'))
    df_projecao_planejado["QUANTITY"] = np.ceil(df_projecao_planejado["QUANTITY"]).astype(int) 
    
    #Exportar como .TXT
    nome_arquivo = "CARGA_FLUXO_SEMANAL_"+data_ref.strftime("%Y.%m.%d")+".txt"
    caminho_completo = os.path.join(base_dir, folder, nome_arquivo)
    df_projecao_planejado.to_csv(caminho_completo, sep="\t", index=False)


def exportar_projecao_PBI(lista_DDMRP_fluxo, lista_materiais, data_ref, df_parametros, df_custo, base_dir, folder,
                          arr_TOG, arr_TOY, arr_TOR, arr_ADU, arr_ESTOQUE, arr_FLUXO_LIQUIDO, arr_planejado, arr_planejado_entrega, arr_DAF, arr_NIPs_completo):

    """Exporta relatórios de projeção para o PowerBI, integra vetores calculados nas
     etapas anteriores em um unico dataframe, insere informações de D0 vindas do relatorio de
     parametros e custo, calcula status do buffer. Exporta 5 arquivos, um para cada tipo de material."""

    #Definir ranges de datas
    datas_projecao = lista_DDMRP_fluxo[1:]
    datas_projecao_atraso = ["ATRASO"] + lista_DDMRP_fluxo

    #Agrupar informações de D+1 ##################################################
    
    ##TOG
    df_TOG = pd.DataFrame(arr_TOG, columns=datas_projecao, index=lista_materiais)
    df_TOG.insert(0, "Material", lista_materiais)
    df_TOG = df_TOG.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='TOG')
    df_TOG = df_TOG.sort_values(by=['Material'])
    
    ##TOY
    df_TOY = pd.DataFrame(arr_TOY, columns=datas_projecao, index=lista_materiais)
    df_TOY.insert(0, "Material", lista_materiais)
    df_TOY = df_TOY.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='TOY')
    df_TOY = df_TOY.sort_values(by=['Material'])
    
    ##TOR
    df_TOR = pd.DataFrame(arr_TOR, columns=datas_projecao, index=lista_materiais)
    df_TOR.insert(0, "Material", lista_materiais)
    df_TOR = df_TOR.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='TOR')
    df_TOR = df_TOR.sort_values(by=['Material'])
    
    ##ADU
    df_ADU = pd.DataFrame(arr_ADU, columns=datas_projecao, index=lista_materiais)
    df_ADU.insert(0, "Material", lista_materiais)
    df_ADU = df_ADU.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='ADU')
    df_ADU = df_ADU.sort_values(by=['Material'])
    
    ##ESTOQUE
    df_EST = pd.DataFrame(arr_ESTOQUE, columns=datas_projecao, index=lista_materiais)
    df_EST.insert(0, "Material", lista_materiais)
    df_EST = df_EST.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='ESTOQUE')
    df_EST = df_EST.sort_values(by=['Material'])
    
    ##FLUXO LIQUIDO
    df_FLU = pd.DataFrame(arr_FLUXO_LIQUIDO, columns=datas_projecao, index=lista_materiais)
    df_FLU.insert(0, "Material", lista_materiais)
    df_FLU = df_FLU.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='FLUXO_LIQUIDO')
    df_FLU = df_FLU.sort_values(by=['Material'])
    
    #VETORES COM D0 e ATRASO #####################################################
    
    ##Planejado
    df_PLA = pd.DataFrame(arr_planejado, columns=lista_DDMRP_fluxo, index=lista_materiais)
    df_PLA.insert(0, "Material", lista_materiais)
    df_PLA = df_PLA.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='PLANEJADO')
    df_PLA_D0 = df_PLA.query('DATA == @data_ref').copy()
    df_PLA_D0 = df_PLA_D0.drop(columns=['DATA'])
    df_PLA = df_PLA[df_PLA['DATA'] > data_ref]
    df_PLA = df_PLA.sort_values(by=['Material'])
    
    ##Planejado Entrega
    df_PLA_ENT = pd.DataFrame(arr_planejado_entrega, columns=lista_DDMRP_fluxo, index=lista_materiais)
    df_PLA_ENT.insert(0, "Material", lista_materiais)
    df_PLA_ENT = df_PLA_ENT.melt(id_vars='Material',
                                var_name='DATA',
                                value_name='PLANEJADO_ENTREGA')
    df_PLA_ENT_D0 = df_PLA_ENT.query('DATA == @data_ref').copy()
    df_PLA_ENT_D0 = df_PLA_ENT_D0.drop(columns=['DATA'])
    df_PLA_ENT = df_PLA_ENT[df_PLA_ENT['DATA'] > data_ref]
    df_PLA_ENT = df_PLA_ENT.sort_values(by=['Material'])
    
    ##DAF
    df_DAF = pd.DataFrame(arr_DAF, columns=lista_DDMRP_fluxo, index=lista_materiais)
    df_DAF.insert(0, "Material", lista_materiais)
    df_DAF = df_DAF.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='DAF')
    df_DAF = df_DAF[df_DAF['DATA'] > data_ref]
    df_DAF = df_DAF.sort_values(by=['Material'])
    
    ##NIPs
    df_NIPs = pd.DataFrame(arr_NIPs_completo, columns=datas_projecao_atraso, index=lista_materiais)
    df_NIPs.insert(0, "Material", lista_materiais)
    df_NIPs = df_NIPs.melt(id_vars='Material',
                        var_name='DATA',
                        value_name='NIPs')
    df_NIPs = df_NIPs[df_NIPs['DATA'] != "ATRASO"]
    df_NIPs_D0 = df_NIPs.query('DATA == @data_ref').copy()
    df_NIPs_D0 = df_NIPs_D0.drop(columns=['DATA'])
    df_NIPs = df_NIPs[df_NIPs['DATA'] > data_ref]
    df_NIPs = df_NIPs.sort_values(by=['Material'])
    
    #Coletar informações de D0
    colunas = ['Material', 'TOR', 'TOY', "TOG", "DAF", "ADU", "ESTOQUE", "FLUXO_LIQUIDO"]
    df_D0 = df_parametros[colunas].copy()
    
    #Inserir informações de D0
    df_D0 = (df_D0
            .set_index('Material')
            .join(df_NIPs_D0.set_index('Material'), how='left')
            .join(df_PLA_D0.set_index('Material'), how='left')
            .join(df_PLA_ENT_D0.set_index('Material'), how='left')
            .reset_index())
    df_D0["DATA"] = data_ref
    
    #Inserir informações de D+1
    df_D1 = (df_TOG
            .set_index(['Material', 'DATA'])
            .join(df_TOY.set_index(['Material', 'DATA']), how='left')
            .join(df_TOR.set_index(['Material', 'DATA']), how='left')
            .join(df_ADU.set_index(['Material', 'DATA']), how='left')
            .join(df_EST.set_index(['Material', 'DATA']), how='left')
            .join(df_FLU.set_index(['Material', 'DATA']), how='left')
            .join(df_PLA.set_index(['Material', 'DATA']), how='left')
            .join(df_PLA_ENT.set_index(['Material', 'DATA']), how='left')
            .join(df_DAF.set_index(['Material', 'DATA']), how='left')
            .join(df_NIPs.set_index(['Material', 'DATA']), how='left')
            .reset_index())
    
    #Empilhar Dataframes
    df_PROJECAO = pd.concat([df_D0, df_D1], ignore_index=True) 
    
    #Colar informações falantes
    #DataRef
    df_PROJECAO['DATA_REF'] = data_ref
    #Entrega
    df_PROJECAO["ADU_AJUSTADA"] = df_PROJECAO["ADU"] * df_PROJECAO["DAF"]
    #ADU_ajustada
    df_PROJECAO["ENTRADA"] = df_PROJECAO["PLANEJADO_ENTREGA"] + df_PROJECAO["NIPs"]
    
    #Status
    tog_safe = df_PROJECAO['TOG'].replace(0, np.nan)
    ratio = df_PROJECAO['FLUXO_LIQUIDO'] / tog_safe
    tor_ratio = df_PROJECAO['TOR'] / tog_safe
    toy_ratio = df_PROJECAO['TOY'] / tog_safe
    conds = [df_PROJECAO['ADU'].fillna(0).eq(0),
            ratio.le(0),
            ratio.le(tor_ratio),
            ratio.le(toy_ratio),
            ratio.le(1),]
    choices = ['SEM BUFFER', 'RUPTURA', 'RISCO', 'BAIXO', 'NORMAL']
    df_PROJECAO['STATUS'] = np.select(conds, choices, default='EXCESSO')
    
    #Custo
    s_mapa = df_custo.set_index('Material')['CUSTO']
    df_PROJECAO['CUSTO'] = df_PROJECAO['Material'].map(s_mapa).fillna(0)
    
    #Tipo do Material
    s_mapa = df_parametros.set_index('Material')['TIPO_MATERIAL']
    df_PROJECAO['TIPO_MATERIAL'] = df_PROJECAO['Material'].map(s_mapa).fillna(0)
    
    #Renomear colundas e reeordenas
    df_PROJECAO = df_PROJECAO.rename(columns={"Material": "MATERIAL"})
    df_PROJECAO = df_PROJECAO.rename(columns={"ADU": "ADU_LIMPA"})
    df_PROJECAO = df_PROJECAO.rename(columns={"ADU_AJUSTADA": "ADU"})
    df_PROJECAO = df_PROJECAO[['DATA_REF','MATERIAL','DATA','PLANEJADO','FLUXO_LIQUIDO','ADU',
                            'TOG','TOY','TOR','CUSTO','STATUS','ENTRADA','ESTOQUE',
                            'ADU_LIMPA','DAF','NIPs','PLANEJADO_ENTREGA','TIPO_MATERIAL']]

    #Exportar separadamente por Tipo de Material
    categorias = ['MATERIA-PRIMA', 'CONSUMIVEL', 'TERCERIZADO', 'MANUFATURADO', 'PRODUTO-PRONTO']
    for cat in categorias:
        df_filtrado = df_PROJECAO[df_PROJECAO['TIPO_MATERIAL'] == cat]
        nome_arquivo = f"HISTORICO_FLUXO_SEMANAL_{cat}.xlsx"
        caminho_completo = os.path.join(base_dir, folder, nome_arquivo)
        df_filtrado.to_excel(caminho_completo, sheet_name="Planilha1", index=False)


def def_exportar_planejado_SAP(df_parametros, df_dado_mestre, base_dir, folder, data_ref):

    """Exporta planejamento para o SAP, utiliza informações de df_parametros, extrai dados
    do dadomestre para calcular UMB. Arquivo gerado em .txt."""

    #Selecionar colunas de interesse de df_parametros
    df_parametros = df_parametros[["Material", "NIP_SUGERIDA", "DATA_ENTREGA"]]

    #Manter apenas registros de interesse (NIP > 0)
    df_parametros = df_parametros[df_parametros['NIP_SUGERIDA'] > 0]

    #Atribuir coluna tipo
    df_parametros["TIPO"] = int(1)

    #Adicionar coluna de unidade
    df_parametros = df_parametros.merge(df_dado_mestre[['Material', 'UMB']], on='Material', how='left')

    #Formatar colunas
    df_parametros["DATA_ENTREGA"] = (pd.to_datetime(df_parametros['DATA_ENTREGA'], errors='coerce').dt.strftime('%d.%m.%Y'))
    df_parametros["NIP_SUGERIDA"] = np.ceil(df_parametros["NIP_SUGERIDA"]).astype(int) 

    #Renomear colunas e ordenar-las
    df_parametros = df_parametros.rename(columns={'Material': 'MATERIAL',
                                                  'DATA_ENTREGA': 'DATA',
                                                  'NIP_SUGERIDA': 'QUANTITY',
                                                  'UMB': 'UOM'})
    df_parametros.columns = ['MATERIAL', 'TIPO', 'DATA', 'QUANTITY', 'UOM']

    #Exportar relatorio como .TXT
    nome_arquivo = "CARGA_SAP_"+data_ref.strftime("%Y.%m.%d")+".txt"
    caminho_completo = os.path.join(base_dir, folder, nome_arquivo)
    df_parametros.to_csv(caminho_completo, sep="\t", index=False)


def def_exportar_planejado_PBI(df_dado_mestre, df_custo, df_parametros,
                               df_ops_total, df_ops_saldo, df_ops_andamento,
                               df_ocs_total, df_ocs_saldo, df_ocs_andamento,
                               lista_materiais, data_ref, base_dir, folder):

    """Exporta informações para serem lidas pelo Power BI, traz parametros manuais e do SAP,
    status e quantidades de OCs e OPs segmentados por tipo e prazo. Informações são armazendas em arquivo .xlsx"""

    #Recolher informações de DadoMestre e renomea-las
    cols_map = {
    "Material": "MATERIAL",
    "Texto breve de material": "DESCRICAO",
    "Denominação": "UNIDADE",
    "Família": "FAMILIA",
    "DenomIndStand.": "DENOMINACAO",
    "RCtrP": "RCTRP",
    "TMat": "TMAT",
    "PlMRP": "PLMRP",
    "TpM": "MRP",
    "TEM": "TEM",
    "PEP": "PEP",
    "Per.seg.": "PER_SEG",
    "CódMargSeg": "COD_M_SEG",
    "TL": "TAM_LOTE",
    "Cal": "CAL",
    "Estq.segurança": "EST_SEG",
    "Pt.reabast.": "ROP",
    "TamMínLote": "LOTE_MIN",
    "Tam.máx.lote": "LOTE_MAX",
    "Tam.fx.lote": "LOTE_FIXO",
    "ValArredond.": "LOTE_MULT",
    "PerfCP": "TIPO_OP",
    "UMB": "UMB",}
    
    cols_presentes = [c for c in cols_map if c in df_dado_mestre.columns]
    df_dado_mestre = df_dado_mestre.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Custo e renomea-las
    cols_map = {
    "Material": "MATERIAL",
    "CUSTO": "CUSTO"}

    cols_presentes = [c for c in cols_map if c in df_custo.columns]
    df_custo = df_custo.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Parametros e renomea-las
    cols_map = {
    "Material": "MATERIAL",
    "MEDIA_CONSUMO": "CONSUMO_MEDIA_30D",
    "DESV_CONSUMO": "CONSUMO_DESVIO_30D",
    "MEDIA_CARTEIRA": "DEMANDA_MEDIA_30D",
    "DESV_CARTEIRA": "DEMANDA_DESVIO_30D",
    "ADU": "ADU_60D",
    "DESV_ADU": "ADU_DESVIO_60D",
    "FATOR VAR": "ADU_FATOR",
    "HML": "ADU_HML",
    "LT FAB": "LT_FAB",
    "LT NEST": "LT_NEST",
    "LT TERC": "LT_TERC",
    "DLT": "DLT",
    "LMS": "LMS",
    "FATOR DLT": "LT_FATOR",
    "CICLO DESEJ.": "CICLO_DESEJ",
    "HORIZ. PICO ORDEM": "HORIZ_DIAS",
    "G1": "G1",
    "G2": "G2",
    "G3": "G3",
    "G": "G",
    "Y": "Y",
    "R1": "R1",
    "R2": "R2",
    "R": "R",
    "ESTOQUE": "EST_QTD",
    "DEMANDA_HOJE": "DEMANDA_HOJE",
    "DEMANDA_PICO": "DEMANDA_PICO",
    "NIPs": "NIPS",
    "FLUXO_LIQUIDO": "FLUXO_LIQUIDO",
    "NIP_SUGERIDA": "NIP_SUGERIDA",
    "DATA_ENTREGA": "DATA_ENTREGA",
    "TERC": "TERCEIRIZADO",
    "TIPO_MATERIAL": "CATEGORIA",
    "DAF": "DAF"}

    cols_presentes = [c for c in cols_map if c in df_parametros.columns]
    df_parametros = df_parametros.loc[:, cols_presentes].rename(columns=cols_map)

    # RELATORIOS DE OCS E OPS #####################################################

    #Recolher informações de Total de OPs
    cols_map = {
    "Material": "MATERIAL",
    "TOTAL_DD": "TOTAL_OPs_ZDD",
    "TOTAL_N_DD": "TOTAL_OPs_N_ZDD",
    "ZPD": "TOTAL_OPS_ZPD",
    "ZPK": "TOTAL_OPS_ZPK",
    "ZPP": "TOTAL_OPS_ZPP",
    "ZPR": "TOTAL_OPS_ZPR",
    "ZPS": "TOTAL_OPS_ZPS",
    "ZPT": "TOTAL_OPS_ZPT"}

    cols_presentes = [c for c in cols_map if c in df_ops_total.columns]
    df_ops_total = df_ops_total.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Saldo de OPs
    cols_map = {
    "Material": "MATERIAL",
    "SALDO_DD": "OPs_ZDD_QTD",
    "SALDO_N_DD": "OPs_N_ZDD_QTD"}

    cols_presentes = [c for c in cols_map if c in df_ops_saldo.columns]
    df_ops_saldo = df_ops_saldo.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Saldo de OCs
    cols_map = {
    "Material": "MATERIAL",
    "DD": "OCs_ZDD_QTD",
    "NAO_DD": "OCs_N_ZDD_QTD"}

    cols_presentes = [c for c in cols_map if c in df_ocs_saldo.columns]
    df_ocs_saldo = df_ocs_saldo.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Total de OCs
    cols_map = {
    "Material": "MATERIAL",
    "DD": "TOTAL_OCs_ZDD",
    "NAO_DD": "TOTAL_OCs_N_ZDD"}

    cols_presentes = [c for c in cols_map if c in df_ocs_total.columns]
    df_ocs_total = df_ocs_total.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Status de OCs
    cols_map = {
    "Material": "MATERIAL",
    "ATRASO": "OCs_EM_ATRASO",
    "ANDAMENTO": "OCs_EM_ANDAMENTO"}

    cols_presentes = [c for c in cols_map if c in df_ocs_andamento.columns]
    df_ocs_andamento = df_ocs_andamento.loc[:, cols_presentes].rename(columns=cols_map)

    #Recolher informações de Status de OPs
    cols_map = {
    "Material": "MATERIAL",
    "ATRASO": "OPs_EM_ATRASO",
    "ANDAMENTO": "OPs_EM_ANDAMENTO"}

    cols_presentes = [c for c in cols_map if c in df_ops_andamento.columns]
    df_ops_andamento = df_ops_andamento.loc[:, cols_presentes].rename(columns=cols_map)

    #Integrar todos os dataframes de Ordens de Produção e Compra
    list_df_ocs_ops = [df_ocs_total, df_ocs_andamento, df_ocs_saldo,
                       df_ops_total, df_ops_andamento, df_ops_saldo]

    df_ocs_ops = reduce(lambda left, right: pd.merge(left, right, on='MATERIAL', how='outer'), list_df_ocs_ops)
    df_ocs_ops = df_ocs_ops.fillna(0)

    #Calcular colunas extras
    df_ocs_ops["OPS_QTD"] = df_ocs_ops["OPs_ZDD_QTD"]+df_ocs_ops["OPs_N_ZDD_QTD"]
    df_ocs_ops["OCS_QTD"] = df_ocs_ops["OCs_ZDD_QTD"]+df_ocs_ops["OCs_N_ZDD_QTD"]
    df_ocs_ops["ORDENS_EM_ATRASO"] = df_ocs_ops["OPs_EM_ATRASO"] + df_ocs_ops["OCs_EM_ATRASO"]
    df_ocs_ops["ORDENS_EM_ANDAMENTO"] = df_ocs_ops["OPs_EM_ANDAMENTO"] + df_ocs_ops["OCs_EM_ANDAMENTO"]

    #Dropar colunas excedentes
    df_ocs_ops.drop(['OPs_EM_ATRASO', 'OCs_EM_ATRASO', 'OPs_EM_ANDAMENTO', 'OCs_EM_ANDAMENTO'], axis=1, inplace=True)

    #Inserir itens faltantes
    df_ocs_ops = (df_ocs_ops.set_index('MATERIAL')
                  .reindex(lista_materiais)
                  .fillna(0)
                  .reset_index())
        
    # COMBINAR DATAFRAMES #########################################################
    
    #Combinar dataframes de parametros, dados mestres e ordens
    df_completo = (df_dado_mestre
                   .merge(df_parametros, on='MATERIAL', how='inner')
                   .merge(df_ocs_ops, on='MATERIAL', how='inner')
                   .merge(df_custo, on='MATERIAL', how='left'))
    df_completo['CUSTO'] = df_completo['CUSTO'].fillna(0)

    #Inserir colunas calculadas
    
    #DATA_REF
    df_completo["DATA_REF"] = data_ref

    #LT_TEM
    df_completo["LT_TEM"] = df_completo["TEM"]

    #LT_FORN
    df_completo["LT_FORN"] = df_completo["PEP"]

    #MOQ
    df_completo["MOQ"] = df_completo["LOTE_MIN"]

    #LIMITE_QTD
    df_completo["LIMITE_QTD"] = np.ceil(df_completo["R1"] + (df_completo["ADU_60D"]*df_completo["DAF"]))

    #BUFFERS
    df_completo["TOR"] = df_completo["R"]
    df_completo["TOY"] = df_completo["R"] + df_completo["Y"]
    df_completo["TOG"] = df_completo["R"] + df_completo["Y"] + df_completo["G"]

    #PLANO_PRIORIDADE
    df_completo["PLANO_PRIORIDADE"] = (df_completo["FLUXO_LIQUIDO"].div(df_completo["TOG"]).where(df_completo["TOG"] != 0, 1))

    #DIM_STATUS_DO_BUFFER
    ratio_tor = np.divide(df_completo["TOR"], df_completo["TOG"],
                          out=np.full(len(df_completo), np.inf, dtype=float),
                          where=df_completo["TOG"].to_numpy() != 0)
    
    ratio_toy = np.divide(df_completo["TOY"], df_completo["TOG"],
                          out=np.full(len(df_completo), np.inf, dtype=float),
                          where=df_completo["TOG"].to_numpy() != 0)
    
    conds = [
        df_completo["TOG"].eq(0),                       # TOG = 0
        df_completo["PLANO_PRIORIDADE"].eq(1),          # PRIOR = 1
        df_completo["PLANO_PRIORIDADE"].le(0),          # PRIOR <= 0
        df_completo["PLANO_PRIORIDADE"].le(ratio_tor),  # PRIOR <= TOR/TOG
        df_completo["PLANO_PRIORIDADE"].le(ratio_toy),  # PRIOR <= TOY/TOG
        df_completo["PLANO_PRIORIDADE"].lt(1),          # PRIOR < 1
        df_completo["PLANO_PRIORIDADE"].gt(1),          # PRIOR > 1
    ]

    choices = ["SEM BUFFER", "NORMAL", "RUPTURA", "RISCO", "BAIXO", "NORMAL", "EXCESSO"]
    df_completo["DIM_STATUS_DO_BUFFER"] = np.select(conds, choices, default=np.nan)

    #PLANO_STATUS
    df_completo["PLANO_STATUS"] = df_completo["DIM_STATUS_DO_BUFFER"]

    #NIVEL_DE_ALERTA
    df_completo["NIVEL_DE_ALERTA"] = df_completo["TOR"]/2

    #EXECUCAO_BUFFER
    df_completo["EXECUCAO_BUFFER"] = (df_completo["EST_QTD"].div(df_completo["TOY"]).where(df_completo["TOY"] != 0, 1))

    #EXECUCAO_STATUS
    ratio_nda = np.divide(df_completo["NIVEL_DE_ALERTA"], df_completo["TOY"],
                          out=np.full(len(df_completo), np.inf, dtype=float),
                          where=df_completo["TOY"].to_numpy() != 0)
    
    ratio_tor = np.divide(df_completo["TOR"], df_completo["TOY"],
                          out=np.full(len(df_completo), np.inf, dtype=float),
                          where=df_completo["TOY"].to_numpy() != 0)
    
    conds = [
        (df_completo["TOG"].eq(0) & df_completo["EST_QTD"].eq(0)),      # TOY = 0
        df_completo["EXECUCAO_BUFFER"].eq(1),                           # PRIOR = 1
        df_completo["EXECUCAO_BUFFER"].le(0),                           # PRIOR <= 0
        df_completo["EXECUCAO_BUFFER"].le(ratio_nda),                   # PRIOR <= NIVEL DE ALERTA / TOY
        df_completo["EXECUCAO_BUFFER"].le(ratio_tor),                   # PRIOR <= TOR / TOY
        df_completo["EXECUCAO_BUFFER"].lt(1),                           # PRIOR < 1
        df_completo["EXECUCAO_BUFFER"].gt(1),                           # PRIOR > 1
    ]

    choices = ["SEM BUFFER", "NORMAL", "RUPTURA", "RISCO", "BAIXO", "NORMAL", "EXCESSO"]
    df_completo["EXECUCAO_STATUS"] = np.select(conds, choices, default=np.nan)
    
    # FORMATAR DATAFRAME ##########################################################
    
    #Colar colunas na ordem
    ordem = [
    "DATA_REF","MATERIAL","DESCRICAO","TMAT","UMB","PLMRP","MRP","TEM","PEP",
    "PER_SEG","COD_M_SEG","TAM_LOTE","CAL","EST_SEG","ROP","LOTE_MIN","LOTE_MAX",
    "LOTE_FIXO","LOTE_MULT","TIPO_OP","CUSTO","CONSUMO_MEDIA_30D","CONSUMO_DESVIO_30D",
    "DEMANDA_MEDIA_30D","DEMANDA_DESVIO_30D","ADU_60D","ADU_DESVIO_60D","ADU_HML","ADU_FATOR",
    "LT_FAB","LT_NEST","LT_TERC","LT_TEM","LT_FORN","DLT","LMS","LT_FATOR","CICLO_DESEJ",
    "MOQ","HORIZ_DIAS","LIMITE_QTD","G1","G2","G3","G","Y","R1","R2","R","EST_QTD","OPS_QTD",
    "OCS_QTD","DIM_STATUS_DO_BUFFER","DEMANDA_HOJE","DEMANDA_PICO","NIPS","FLUXO_LIQUIDO",
    "PLANO_PRIORIDADE","PLANO_STATUS","NIP_SUGERIDA","DATA_ENTREGA","NIVEL_DE_ALERTA",
    "EXECUCAO_BUFFER","EXECUCAO_STATUS","ORDENS_EM_ATRASO","ORDENS_EM_ANDAMENTO",
    "OPs_ZDD_QTD","OPs_N_ZDD_QTD","OCs_ZDD_QTD","OCs_N_ZDD_QTD","TOTAL_OPs_ZDD",
    "TOTAL_OPs_N_ZDD","TOTAL_OCs_ZDD","TOTAL_OCs_N_ZDD","UNIDADE","FAMILIA","DENOMINACAO",
    "RCTRP","TERCEIRIZADO","TOTAL_OPS_ZPD","TOTAL_OPS_ZPK","TOTAL_OPS_ZPP","TOTAL_OPS_ZPR",
    "TOTAL_OPS_ZPS","TOTAL_OPS_ZPT","CATEGORIA","DAF"]

    df_completo = df_completo[ordem]

    # EXPORTAR DATAFRAME ##########################################################
    nome_arquivo = "HISTORICO_"+data_ref.strftime("%Y.%m.%d")+".xlsx"
    caminho_completo = os.path.join(base_dir, folder, nome_arquivo)
    df_completo.to_excel(caminho_completo, sheet_name="Planilha1", index=False)