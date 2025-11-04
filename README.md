# ETL-magic

Projeto ETL simples para coletar, transformar e persistir dados de cards do Scryfall (Magic: The Gathering).

## Descrição

Este repositório contém um pipeline ETL em Python dividido em três camadas:

- Bronze: extração de dados brutos da API do Scryfall e armazenamento em JSON.
- Silver: transformação/limpeza dos dados e exportação para CSV.
- Gold: agregação e carga em um data warehouse SQLite.

O script principal é `etl_magic.py` e organiza as etapas em funções reutilizáveis para cada camada.

## Estrutura do repositório

```
Dockerfile
etl_magic.py            # Script principal com pipelines Bronze / Silver / Gold
requirements.txt       # Dependências do projeto
README.md
bronze/                # Saída da camada Bronze (raw_cards.json)
	raw_cards.json
silver/                # Saída da camada Silver (refined_cards.csv)
gold/                  # Saída da camada Gold (data warehouse SQLite)
	magic_data_warehouse.db (gerado)
refined_cards.csv      # Exemplo/artefato CSV (padrão do projeto)
```

## Pré-requisitos

- Python 3.8+ instalado
- pip
- (Opcional) Docker, se quiser executar via container

## Instalação (virtualenv recomendado)

No PowerShell (Windows):

```powershell
# criar e ativar venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar dependências
pip install -r requirements.txt
```

Ou, sem virtualenv:

```powershell
pip install -r requirements.txt
```

## Como usar

O script `etl_magic.py` executa as três camadas em sequência quando chamado como script principal. Execute no diretório do projeto:

```powershell
python etl_magic.py
```

Isso irá:

- Baixar os dados da coleção configurada (`SET_CODE = 'mh3'` por padrão) e salvar em `bronze/raw_cards.json`.
- Transformar e salvar o CSV em `silver/refined_cards.csv`.
- Gerar o data warehouse SQLite em `gold/magic_data_warehouse.db` contendo as tabelas `dim_cartas` e `fact_resumo_colecao`.

Se quiser executar apenas uma camada, importe as funções do script ou modifique o bloco `if __name__ == "__main__"` conforme necessário.

## Parâmetros e personalização

- `SET_CODE` dentro de `etl_magic.py` define a coleção a ser consultada na API do Scryfall. Altere para outros códigos de set conforme desejado.
- Paths das camadas estão definidos nas constantes `BRONZE_PATH`, `SILVER_PATH` e `GOLD_PATH`.

## Uso com Docker (opcional)

Build da imagem:

```powershell
docker build -t meu-etl-magic .
```

Executar container (montando o diretório atual para persistir artefatos):

```powershell
docker run -v "$(pwd):/app" meu-etl-magic
```

Observação: em Windows, a montagem de volume com `${PWD}` no PowerShell geralmente funciona, mas dependendo da configuração do Docker Desktop pode ser necessário ajustar o caminho (ex.: `C:\path\to\repo`) ou usar WSL.

## Saídas e artefatos

- `bronze/raw_cards.json` — dados brutos obtidos da API
- `silver/refined_cards.csv` — dados limpos e normalizados
- `gold/magic_data_warehouse.db` — banco SQLite com tabelas dimensionais e de fatos

## Dependências

Ver `requirements.txt`. Principais pacotes:

- requests
- pandas
- sqlalchemy

## Contribuição

Contribuições são bem-vindas. Abra issues ou pull requests com melhorias, correções de bugs ou novos recursos.

