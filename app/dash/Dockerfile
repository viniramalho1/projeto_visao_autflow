FROM python:3.9-slim

WORKDIR /usr/src/app

# Copie os arquivos para o contêiner
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponha a porta do Streamlit
EXPOSE 8501

# Comando padrão para rodar o Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
