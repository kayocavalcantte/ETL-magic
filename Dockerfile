# Dockerfile

# 1. Imagem Base: Começamos com uma imagem oficial do Python
FROM python:3.10-slim

# 2. Diretório de Trabalho: Criamos uma pasta "app" dentro do container
WORKDIR /app

# 3. Copiar o arquivo de dependências PRIMEIRO
# (Isso otimiza o cache do Docker)
COPY requirements.txt .

# 4. Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o seu script para dentro da imagem
COPY etl_magic.py .

# 6. Comando para rodar: Quando o container iniciar, execute o script
CMD [ "python", "./etl_magic.py" ]