# Use a imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /usr/src/app

# Copie os arquivos da aplicação para o contêiner
COPY . .

# Atualize o apt-get, instale as dependências do sistema necessárias e limpe os caches
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Instale as dependências do Python especificadas no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta que a aplicação usará
EXPOSE 5000

# Comando para iniciar a aplicação usando Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
