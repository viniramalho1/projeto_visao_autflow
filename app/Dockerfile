# Use a imagem base oficial do Python
FROM python:3.9-slim

WORKDIR /usr/src/app

COPY . .

# Instale as dependências necessárias para o mysqlclient
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta que a aplicação vai rodar
EXPOSE 5000

# Comando para rodar a aplicação usando Gunicorn
CMD ["python3", "app.py"]
