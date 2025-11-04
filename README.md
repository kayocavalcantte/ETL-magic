# ETL-magic

### Projeto ETL para Técnicas de Integração de Sistemas

Projeto de pipeline ETL desenvolvido para a disciplina de Técnicas de Integração de Sistemas. O objetivo é implementar um pipeline completo de extração, transformação e carga usando uma base de dados pública (a API do Scryfall - Magic: The Gathering).

O projeto segue a arquitetura Medallion, organizando o armazenamento em três camadas de dados: Bronze, Silver e Gold.

📜 Relatório do Processo ETL
Esta seção documenta o processo de desenvolvimento, conforme solicitado nas instruções do trabalho.

1. Fonte dos Dados e Justificativa da Escolha

Fonte: Scryfall API

Justificativa: A Scryfall API é uma base de dados pública de livre acesso, robusta e muito bem documentada, que fornece dados complexos sobre o card game Magic: The Gathering. Ela foi escolhida por:

- Riqueza de Dados: Cada "carta" é um registro com dezenas de atributos (custos, textos, tipos, poder, etc.).
- Desafio de Transformação: Os dados vêm em JSON aninhado, com campos polimórficos (ex: cartas que não são criaturas não têm power/toughness) e listas, o que torna a etapa de transformação (Silver) interessante.
- Formato Aberto: A API serve os dados em JSON, um dos formatos abertos sugeridos.

2. Estrutura e Formato dos Dados Originais

Formato: JSON.

Estrutura: A API (no endpoint `/cards/search`) retorna um objeto JSON paginado. O campo `data` contém uma lista de objetos, onde cada objeto representa uma carta.

Camada Bronze: Os dados brutos (a lista extraída do campo `data`) são salvos sem qualquer modificação no arquivo `bronze/raw_cards.json`. Um exemplo de um objeto de carta (simplificado) é:

```json
{
	"id": "000001a1-0000-0000-0000-000000000001",
	"name": "Anjo Serra",
	"mana_cost": "{3}{W}{W}",
	"cmc": 5.0,
	"type_line": "Creature — Angel",
	"oracle_text": "Flying, vigilance",
	"power": "4",
	"toughness": "4",
	"rarity": "uncommon",
	"set": "mh3",
	"artist": "Mark Poole"
	// ... e dezenas de outros campos
}
```

3. Etapas de Transformação Aplicadas

O pipeline é dividido em duas grandes etapas de transformação:

A. Bronze ➔ Silver (Limpeza e Normalização)

Nesta fase, lemos o `bronze/raw_cards.json` e aplicamos as seguintes transformações para gerar uma tabela limpa:

- Carregamento: O JSON bruto é carregado em um DataFrame pandas.
- Seleção de Colunas: Apenas as colunas de interesse são mantidas (ex: id, name, mana_cost, cmc, type_line, oracle_text, power, toughness, rarity, set, artist).
- Tratamento de Nulos: Campos que podem estar ausentes (como power, toughness em cartas que não são criaturas, ou mana_cost em terrenos) são preenchidos com o valor padrão `'N/A'`.
- Engenharia de Features (Enriquecimento): A coluna `type_line` (ex: "Creature — Eldrazi") é dividida em duas novas colunas: `tipo_principal` ("Creature") e `subtipo` ("Eldrazi").
- Padronização: A coluna `cmc` (custo de mana convertido) é garantida como um tipo numérico.

Saída: O DataFrame limpo é salvo em formato aberto CSV, em `silver/refined_cards.csv`.

B. Silver ➔ Gold (Agregação e Carga)

Nesta fase, lemos o `silver/refined_cards.csv` para criar o Data Warehouse final, pronto para análise:

- Carregamento: O CSV limpo é lido para um novo DataFrame.
- Criação de Agregações: Uma nova tabela (Fato) é criada. Nós agrupamos os dados por `colecao`, `raridade` e `tipo_principal` e calculamos agregações, como a `contagem_cartas` e o `custo_medio_mana`.
- Carga no DW: O banco de dados SQLite (`gold/magic_data_warehouse.db`) é criado e duas tabelas são carregadas.

4. Modelo de Dados Final da Camada Gold

O Data Warehouse (`magic_data_warehouse.db`) representa o conjunto final de dados prontos para análise. Ele contém duas tabelas, seguindo um modelo dimensional simples:

dim_cartas (Tabela de Dimensão):

Contém os dados limpos da camada Silver (uma linha por carta).

Colunas: `id`, `nome`, `custo_mana`, `custo_convertido`, `poder`, `resistencia`, `raridade`, `artista`, `tipo_principal`, `subtipo`, etc.

fact_resumo_colecao (Tabela de Fatos):

Contém os dados agregados, prontos para BI/Análise.

Colunas: `colecao`, `raridade`, `tipo_principal`, `contagem_cartas`, `custo_medio_mana`.

5. Desafios Encontrados e Soluções Adotadas

Desafio (Extração): A API da Scryfall implementa paginação. Uma única chamada não retorna todas as cartas de uma coleção, apenas os 175 primeiros resultados.

Solução: O script de extração (`extrair_dados_scryfall`) foi implementado com um loop `while`. Ele verifica o campo `has_more` na resposta da API e, se for `True`, faz uma nova requisição para a URL fornecida no campo `next_page`, acumulando os resultados até que todos os dados sejam baixados.

Desafio (Transformação): Os dados são polimórficos. Cartas de "Terreno", por exemplo, não possuem `mana_cost` ou `power`. Isso gera dados nulos (`None` ou `NaN`) que quebram a carga no banco de dados.

Solução: Na etapa Silver, usamos `pandas.fillna('N/A')` para padronizar todos os campos textuais ausentes e `fillna(0)` para campos numéricos (como `cmc`), garantindo que o esquema da tabela final seja consistente e robusto.

Desafio (Ambiente): Garantir que o pipeline rode em qualquer máquina, independente das versões de Python ou bibliotecas instaladas localmente.

Solução: O projeto inclui um `requirements.txt` para ambientes virtuais e um `Dockerfile` que "empacota" o script e suas dependências (pandas, requests, sqlalchemy), permitindo a execução isolada e reprodutível com um único comando Docker.

⚙️ Instruções de Execução do Pipeline
Estrutura do repositório

```
Dockerfile
etl_magic.py          # Script principal com pipelines Bronze / Silver / Gold
requirements.txt      # Dependências do projeto
README.md             # Este arquivo (Relatório)
bronze/               # (Gerado) Saída da camada Bronze
silver/               # (Gerado) Saída da camada Silver
gold/                 # (Gerado) Saída da camada Gold
```

Pré-requisitos

- Python 3.8+
- (Opcional) Docker

Instalação Local (virtualenv recomendado)
No PowerShell (Windows):

```powershell
# criar e ativar venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar dependências
pip install -r requirements.txt
```

Como Usar
O script `etl_magic.py` executa as três camadas em sequência.

```powershell
python etl_magic.py
```

Isso irá popular as pastas `bronze/`, `silver/` e `gold/` com seus respectivos artefatos.

Personalização: Para alterar a coleção (set) do Magic a ser baixada, altere a variável `SET_CODE = 'mh3'` dentro do `etl_magic.py`.

Uso com Docker (Recomendado)
O Docker executa o pipeline em um ambiente controlado.

1. Construir a Imagem: (Execute no terminal, na pasta do projeto)

```powershell
docker build -t meu-etl-magic .
```

2. Executar o Container: Este comando executa o pipeline e usa um "volume" (-v) para que os arquivos gerados (nas pastas `bronze/`, `silver/`, `gold/`) apareçam na sua máquina local.

```powershell
# Para PowerShell no Windows
docker run -v "${PWD}:/app" meu-etl-magic

# Para Linux / Mac / Git Bash
docker run -v "$(pwd):/app" meu-etl-magic
```


