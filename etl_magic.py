import requests
import pandas as pd
from sqlalchemy import create_engine
import time
import os 
import json

BRONZE_PATH = 'bronze'
SILVER_PATH = 'silver'
GOLD_PATH = 'gold'
SET_CODE = 'mh3' 


def extrair_dados_scryfall(set_code):
    """(Função de Extração Pura) Apenas busca os dados na API."""
    print(f"Buscando dados brutos da coleção: {set_code}...")
    url_base = f"https://api.scryfall.com/cards/search?q=set:{set_code}"
    
    todas_as_cartas = []
    url_pagina_atual = url_base

    while url_pagina_atual:
        try:
            response = requests.get(url_pagina_atual)
            response.raise_for_status() 
            data = response.json()
            
            todas_as_cartas.extend(data['data'])
            
            if data['has_more']:
                url_pagina_atual = data['next_page']
                print(f"Buscando próxima página... ({len(todas_as_cartas)} cartas até agora)")
                time.sleep(0.1)
            else:
                url_pagina_atual = None
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados: {e}")
            url_pagina_atual = None
            
    return todas_as_cartas

def transformar_dados_silver(lista_cartas):
    """(Função de Transformação Pura) Limpa os dados brutos."""
    if not lista_cartas:
        return None
        
    df = pd.DataFrame(lista_cartas)
    
    colunas_desejadas = [
        'id', 'name', 'mana_cost', 'cmc', 'type_line', 
        'oracle_text', 'power', 'toughness', 'rarity', 'set', 'artist'
    ]
    
    for col in colunas_desejadas:
        if col not in df.columns:
            df[col] = None
            
    df_transformado = df[colunas_desejadas].copy()

    df_transformado['power'] = df_transformado['power'].fillna('N/A')
    df_transformado['toughness'] = df_transformado['toughness'].fillna('N/A')
    df_transformado['oracle_text'] = df_transformado['oracle_text'].fillna('')
    df_transformado['mana_cost'] = df_transformado['mana_cost'].fillna('N/A')

    split_type = df_transformado['type_line'].str.split(' — ', n=1, expand=True)
    df_transformado['tipo_principal'] = split_type[0]
    df_transformado['subtipo'] = split_type[1].fillna('N/A')
    
    df_transformado = df_transformado.rename(columns={
        'name': 'nome',
        'mana_cost': 'custo_mana',
        'cmc': 'custo_convertido',
        'oracle_text': 'texto_descricao',
        'power': 'poder',
        'toughness': 'resistencia',
        'rarity': 'raridade',
        'set': 'colecao',
        'artist': 'artista'
    })
    
    df_transformado = df_transformado.drop(columns=['type_line']) 
    
    df_transformado['custo_convertido'] = pd.to_numeric(df_transformado['custo_convertido'], errors='coerce').fillna(0)

    return df_transformado


def executar_pipeline_bronze():
    """
    Camada Bronze: Extrai dados e salva como JSON bruto.
    """
    print("\n--- Iniciando Camada BRONZE ---")
    os.makedirs(BRONZE_PATH, exist_ok=True)
    
    dados_brutos = extrair_dados_scryfall(SET_CODE)
    
    if dados_brutos:
        caminho_arquivo = os.path.join(BRONZE_PATH, 'raw_cards.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_brutos, f, ensure_ascii=False, indent=4)
        print(f"Camada Bronze concluída. Dados brutos salvos em: {caminho_arquivo}")
    else:
        print("Falha na Camada Bronze: Nenhum dado extraído.")

def executar_pipeline_silver():
    """
    Camada Silver: Lê o JSON bruto, limpa e salva como CSV.
    """
    print("\n--- Iniciando Camada SILVER ---")
    os.makedirs(SILVER_PATH, exist_ok=True)
    caminho_bronze = os.path.join(BRONZE_PATH, 'raw_cards.json')
    
    try:
        with open(caminho_bronze, 'r', encoding='utf-8') as f:
            dados_brutos = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {caminho_bronze} não encontrado. Rode a camada Bronze primeiro.")
        return

    df_silver = transformar_dados_silver(dados_brutos)
    
    if df_silver is not None:
        caminho_arquivo = os.path.join(SILVER_PATH, 'refined_cards.csv')
        df_silver.to_csv(caminho_arquivo, index=False, encoding='utf-8')
        print(f"Camada Silver concluída. Dados limpos salvos em: {caminho_arquivo}")
    else:
        print("Falha na Camada Silver: Transformação não gerou dados.")

def executar_pipeline_gold():
    """
    Camada Gold: Lê o CSV limpo, agrega e salva no Data Warehouse (SQLite).
    """
    print("\n--- Iniciando Camada GOLD ---")
    os.makedirs(GOLD_PATH, exist_ok=True)
    caminho_silver = os.path.join(SILVER_PATH, 'refined_cards.csv')

    try:
        df_silver = pd.read_csv(caminho_silver)
    except FileNotFoundError:
        print(f"Erro: Arquivo {caminho_silver} não encontrado. Rode a camada Silver primeiro.")
        return

    tabela_dimensao = df_silver
    print("Tabela 'dim_cartas' preparada.")

    print("Criando tabela agregada 'fact_resumo_colecao'...")
    tabela_fato = df_silver.groupby(['colecao', 'raridade', 'tipo_principal']).agg(
        contagem_cartas=('id', 'count'),
        custo_medio_mana=('custo_convertido', 'mean')
    ).reset_index()
    
    tabela_fato['custo_medio_mana'] = tabela_fato['custo_medio_mana'].round(2)

    caminho_db = os.path.join(GOLD_PATH, 'magic_data_warehouse.db')
    engine = create_engine(f'sqlite:///{caminho_db}')
    
    try:
        tabela_dimensao.to_sql('dim_cartas', engine, if_exists='replace', index=False)
        print(f"Tabela 'dim_cartas' carregada no DW com {len(tabela_dimensao)} linhas.")
        
        tabela_fato.to_sql('fact_resumo_colecao', engine, if_exists='replace', index=False)
        print(f"Tabela 'fact_resumo_colecao' carregada no DW com {len(tabela_fato)} linhas.")
        
        print(f"Camada Gold concluída. Data Warehouse salvo em: {caminho_db}")
    
    except Exception as e:
        print(f"Erro ao carregar dados na Camada Gold: {e}")

if __name__ == "__main__":
    executar_pipeline_bronze()
    executar_pipeline_silver()
    executar_pipeline_gold()