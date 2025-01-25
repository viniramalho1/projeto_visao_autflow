import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Configurações do banco de dados
DB_USER = "seu_usuario"
DB_PASS = "sua_senha"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "sua_base"

# Criando a conexão
def get_connection():
    connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    return engine

# Função para buscar dados do banco
def fetch_data(query):
    engine = get_connection()
    with engine.connect() as connection:
        data = pd.read_sql(query, connection)
    return data

# Streamlit App
st.title("Dashboard - Dados do Banco de Dados")

try:
    # Escreva sua query aqui
    query = "SELECT * FROM sua_tabela LIMIT 10"
    df = fetch_data(query)
    st.write("Dados do Banco de Dados:")
    st.dataframe(df)
except Exception as e:
    st.error("Erro ao conectar ou buscar dados do banco.")
    st.write(f"Detalhes do erro: {e}")
