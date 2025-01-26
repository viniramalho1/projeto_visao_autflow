import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# Função para conectar ao banco de dados
def connect_to_database():
    try:
        conn = psycopg2.connect(
            host="192.168.183.1",  # Substitua pelo seu hostname ou IP
            port=5432,             # Porta configurada no PostgreSQL
            database="postgres",   # Nome do banco de dados
            user="meu_usuario",    # Usuário do banco
            password="minha_senha" # Senha do banco
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Erro de conexão ao banco de dados: {e}")
        return None

# Função para executar consultas SQL
def execute_query(query, conn):
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            if query.strip().lower().startswith("select"):
                return cur.fetchall(), [desc[0] for desc in cur.description]
            conn.commit()
            return None, None
    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return None, None

def main():
    st.title("Dashboard de Visualização de Dados")
    st.write("Explore dados diretamente do banco PostgreSQL e visualize gráficos interativos.")

    # Conexão com o banco de dados
    conn = connect_to_database()
    if not conn:
        st.stop()

    # Consulta para obter dados
    query = "SELECT * FROM num_piscar_de_olhos.regiao_administrativa;"  # Ajuste conforme necessário
    data, columns = execute_query(query, conn)

    if data and columns:
        df = pd.DataFrame(data, columns=columns)

        st.subheader("Gráficos")
        col1, col2 = st.columns(2)

        st.subheader("Outro Gráfico Interativo")
        fig3 = px.scatter(df, x=df.columns[0], y=df.columns[1], title="Gráfico de Dispersão")
        st.plotly_chart(fig3)

        st.subheader("Relatórios")
        col3, col4 = st.columns(2)
        

        with col1:
            fig1 = px.bar(df, x=df.columns[0], y=df.columns[1], title="Gráfico de Barras")
            st.plotly_chart(fig1)

        with col2:
            fig2 = px.line(df, x=df.columns[0], y=df.columns[1], title="Gráfico de Linhas")
            st.plotly_chart(fig2)
        
        with col3:
            st.dataframe(df)

        with col4:
            st.dataframe(df)

    else:
        st.warning("Nenhum dado disponível na tabela para exibir.")

    # Finaliza a conexão
    conn.close()

if __name__ == "__main__":
    main()
