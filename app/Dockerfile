FROM python:3.9-slim

WORKDIR /usr/src/app

# Copia o conteúdo da aplicação para o container
COPY . .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta em que o Flask vai rodar
EXPOSE 5000

# Comando para iniciar o Flask
CMD ["python3" ,"app.py"]
