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
            # Se a consulta for do tipo SELECT, retorna dados e nomes de colunas
            if query.strip().lower().startswith("select"):
                return cur.fetchall(), [desc[0] for desc in cur.description]
            conn.commit()
            return None, None
    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return None, None

def main():
    st.title("Dashboard com PostgreSQL e Streamlit")
    st.write("Conecte-se ao banco de dados e visualize os dados interativamente.")
    
    # Conexão com o banco de dados
    conn = connect_to_database()
    if not conn:
        st.stop()
    
    # Menu lateral de opções
    menu = ["Visualizar Dados", "Gráfico Interativo", "Inserir Dados", "Excluir Dados"]
    choice = st.sidebar.selectbox("Escolha uma opção", menu)
    
    # 1. Visualizar Dados
    if choice == "Visualizar Dados":
        st.subheader("Tabela de Dados")
        query = "SELECT * FROM public.teste;"  # Substitua pelo nome exato da sua tabela
        data, columns = execute_query(query, conn)
        
        if data and columns:
            df = pd.DataFrame(data, columns=columns)
            st.dataframe(df)
        else:
            st.warning("Nenhum dado encontrado na tabela.")
    
    # 2. Gráfico Interativo
    elif choice == "Gráfico Interativo":
        st.subheader("Gráfico com Dados")
        query = "SELECT * FROM public.teste;"  # Substitua pelo nome exato da sua tabela
        data, columns = execute_query(query, conn)
        
        if data and columns:
            df = pd.DataFrame(data, columns=columns)
            
            # Selecionar colunas para o eixo X e Y
            x_axis = st.selectbox("Selecione o eixo X", df.columns, key="x_axis")
            y_axis = st.selectbox("Selecione o eixo Y", df.columns, key="y_axis")
            
            # Botão para gerar o gráfico
            if st.button("Gerar Gráfico"):
                # Verifica se a coluna selecionada para o eixo Y é numérica
                if pd.api.types.is_numeric_dtype(df[y_axis]):
                    fig = px.bar(df, x=x_axis, y=y_axis, title="Gráfico Interativo")
                    st.plotly_chart(fig)
                else:
                    st.error(f"A coluna '{y_axis}' precisa ser numérica para criar o gráfico.")
        else:
            st.warning("Nenhum dado disponível na tabela para exibir.")
    
    # 3. Inserir Dados
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
            INSERT INTO public.teste (nome, idade, email, cidade)
            VALUES ('{nome}', {idade}, '{email}', '{cidade}');
            """
            _, _ = execute_query(insert_query, conn)
            st.success("Registro inserido com sucesso!")
    
    # 4. Excluir Dados
    elif choice == "Excluir Dados":
        st.subheader("Excluir Registro")
        id_registro = st.number_input("ID do Registro para excluir", min_value=0, step=1)
        
        if st.button("Excluir"):
            delete_query = f"DELETE FROM public.teste WHERE id = {id_registro};"
            _, _ = execute_query(delete_query, conn)
            st.success("Registro excluído com sucesso!")
    
    # Finaliza a conexão
    conn.close()

if __name__ == "__main__":
    main()
