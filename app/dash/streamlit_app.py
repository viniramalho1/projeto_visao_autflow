import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

st.set_page_config(layout="wide")


# Configurações para conectar ao banco de dados PostgreSQL
def connect_db():
    return psycopg2.connect(
        host="192.168.183.1",  # Substitua pelo seu hostname ou IP
        port=5432,             # Porta configurada no PostgreSQL
        database="postgres",   # Nome do banco de dados
        user="meu_usuario",    # Usuário do banco
        password="minha_senha" # Senha do banco
    )

def load_data(query):
    conn = connect_db()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Consultas para carregar os dados necessários
regiao_data = load_data("SELECT * FROM num_piscar_de_olhos.regiao_administrativa;")
escola_data = load_data("""
    SELECT e.nome AS escola, r.nome AS regiao, COUNT(a.ID_Aluno) AS total_alunos, ed.latitude, ed.longitude
    FROM num_piscar_de_olhos.escola e
    JOIN num_piscar_de_olhos.endereco ed ON e.ID_Endereco = ed.ID_Endereco
    JOIN num_piscar_de_olhos.regiao_administrativa r ON ed.ID_Regiao = r.ID_Regiao
    LEFT JOIN num_piscar_de_olhos.aluno a ON a.ID_Escola = e.ID_Escola
    GROUP BY e.nome, r.nome, ed.latitude, ed.longitude;
""")
exame_data = load_data("""
    SELECT a.nome AS aluno, e.data_exame, e.esferico_OD, e.cilindrico_OD, e.tamanho_pupila_OD, e.tamanho_pupila_OS
    FROM num_piscar_de_olhos.exame e
    JOIN num_piscar_de_olhos.aluno a ON e.ID_Aluno = a.ID_Aluno;
""")

# Adicionar "Todos" ao filtro de regiões
regioes_unicas = ["Todos"] + list(regiao_data["nome"].unique())
st.sidebar.title("Filtros")
selected_regiao = st.sidebar.selectbox("Selecione a Região", regioes_unicas)

# Filtrando dados por região (se "Todos" for selecionado, exibe todos)
if selected_regiao == "Todos":
    filtered_escola_data = escola_data
else:
    filtered_escola_data = escola_data[escola_data["regiao"] == selected_regiao]

# Filtro de coluna numérica para gráfico de exames
numerical_columns = ["esferico_od", "cilindrico_od", "tamanho_pupila_od", "tamanho_pupila_os"]
selected_column = st.sidebar.selectbox("Selecione a Coluna Numérica para o Gráfico de Exames", numerical_columns)

# Filtro de intervalo numérico para a coluna selecionada
min_value = exame_data[selected_column].min()
max_value = exame_data[selected_column].max()
selected_range = st.sidebar.slider(
    f"Selecione o Intervalo de {selected_column.replace('_', ' ').capitalize()}",
    min_value=min_value,
    max_value=max_value,
    value=(min_value, max_value)
)

# Filtrando os dados de exame com base no intervalo selecionado
filtered_exame_data = exame_data[
    (exame_data[selected_column] >= selected_range[0]) &
    (exame_data[selected_column] <= selected_range[1])
]

# Visualizações
st.title("Dashboard Escolar")

# Gráfico de Total de Alunos por Escola na Região Selecionada
fig_escola = px.bar(
    filtered_escola_data,
    x="escola",
    y="total_alunos",
    color="regiao",
    title=f"Total de Alunos por Escola na Região {selected_regiao}"
)
st.plotly_chart(fig_escola)

# Mapa de Localização das Escolas
st.subheader("Mapa de Localização das Escolas")
fig_mapa = px.scatter_mapbox(
    filtered_escola_data,
    lat="latitude",
    lon="longitude",
    hover_name="escola",
    hover_data={"regiao": True, "total_alunos": True},
    color="regiao",
    zoom=5,  # Ajuste o zoom inicial conforme necessário
    mapbox_style="carto-positron",
    title="Localização das Escolas por Região"
)
st.plotly_chart(fig_mapa)

# Gráfico de Exames por Aluno com base no filtro de intervalo
st.subheader("Dados de Exames")
fig_exame = px.scatter(
    filtered_exame_data,
    x="data_exame",
    y=selected_column,  # Use a coluna selecionada no filtro
    color="aluno",
    title=f"{selected_column.replace('_', ' ').capitalize()} por Data de Exame (Intervalo Selecionado)"
)
st.plotly_chart(fig_exame)

# Exibição de tabelas
st.subheader("Detalhes das Escolas")
st.dataframe(filtered_escola_data)

st.subheader("Dados de Exames")
st.dataframe(filtered_exame_data)
