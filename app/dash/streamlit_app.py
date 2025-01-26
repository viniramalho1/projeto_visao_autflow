import streamlit as st
import psycopg2
import pandas as pd

# Função para conectar ao banco de dados
def connect_to_database():
    try:
        conn = psycopg2.connect(
            host="192.168.183.1",  # Substitua pelo hostname correto
            port=5432,  # Porta configurada no PostgreSQL
            database="postgres",  # Nome do banco
            user="meu_usuario",  # Usuário do banco
            password="minha_senha"  # Senha do banco
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

# Interface do Streamlit
def main():
    st.title("Aplicação Streamlit com PostgreSQL")
    st.write("Conecte-se ao banco de dados e visualize os dados.")
    
    # Conexão com o banco de dados
    conn = connect_to_database()
    if not conn:
        st.stop()
    
    # Menu de opções
    menu = ["Visualizar Dados", "Inserir Dados", "Excluir Dados"]
    choice = st.sidebar.selectbox("Escolha uma opção", menu)
    
    if choice == "Visualizar Dados":
        st.subheader("Tabela de Dados")
        query = "select * from public.teste t;"  # Substitua pelo nome da tabela
        data, columns = execute_query(query, conn)
        if data and columns:
            df = pd.DataFrame(data, columns=columns)
            st.dataframe(df)
    
    elif choice == "Inserir Dados":
        st.subheader("Inserir Novo Registro")
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome")
            idade = st.number_input("Idade", min_value=0, step=1)
        
        with col2:
            email = st.text_input("Email")
            cidade = st.text_input("Cidade")
        
        if st.button("Inserir"):
            insert_query = f"""
            INSERT INTO sua_tabela (nome, idade, email, cidade)
            VALUES ('{nome}', {idade}, '{email}', '{cidade}');
            """
            _, _ = execute_query(insert_query, conn)
            st.success("Registro inserido com sucesso!")
    
    elif choice == "Excluir Dados":
        st.subheader("Excluir Registro")
        id_registro = st.number_input("ID do Registro para excluir", min_value=0, step=1)
        
        if st.button("Excluir"):
            delete_query = f"DELETE FROM sua_tabela WHERE id = {id_registro};"
            _, _ = execute_query(delete_query, conn)
            st.success("Registro excluído com sucesso!")
    
    # Fecha a conexão com o banco de dados
    conn.close()

if __name__ == "__main__":
    main()
