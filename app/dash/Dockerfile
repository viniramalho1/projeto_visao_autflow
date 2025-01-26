FROM python:3.9-slim

WORKDIR /usr/src/app

# Copie os arquivos para o contêiner
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponha a porta do Streamlit
EXPOSE 8501

# Comando padrão para rodar o Streamlit
<<<<<<< HEAD
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
=======
CMD ["streamlit", "run", "streamlit_app.py"]
>>>>>>> d2c75242f29033c66abbfd10200abe4ae2e5a555
