import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Escolar",
    page_icon=":school:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização personalizada com CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    h1, h2, h3 {
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Conexão com o banco de dados PostgreSQL
def connect_db():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="meu_usuario",
        password="minha_senha"
    )

# Função para carregar dados com cache
@st.cache_data
def load_data(query):
    conn = connect_db()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Carregar os dados necessários
regiao_data = load_data("SELECT * FROM regiao_administrativa;")
aluno_data = load_data("SELECT * FROM aluno;")
escola_data = load_data(""" 
    SELECT e.id_escola, e.nome AS escola, r.nome AS regiao, COUNT(a.id_aluno) AS total_alunos, ed.latitude, ed.longitude 
    FROM escola e
    JOIN endereco ed ON e.id_endereco = ed.id_endereco
    JOIN regiao_administrativa r ON ed.id_regiao = r.id_regiao
    LEFT JOIN aluno a ON a.id_escola = e.id_escola
    GROUP BY e.id_escola, e.nome, r.nome, ed.latitude, ed.longitude;
""")
exame_data = load_data(""" 
    SELECT a.id_aluno, a.nome AS aluno, e.data_exame, e.esferico_od, e.cilindrico_od, e.tamanho_pupila_od, e.tamanho_pupila_os 
    FROM exame e 
    JOIN aluno a ON e.id_aluno = a.id_aluno;
""")

# Converter a coluna total_alunos para numérico
escola_data["total_alunos"] = pd.to_numeric(escola_data["total_alunos"], errors="coerce").fillna(0).astype(int)

# Paleta de cores análogas (baseada em azul)
analogous_colors = ['#1f77b4', '#4a90e2', '#2a5d8e', '#6baed6', '#08306b']

# Filtros interativos na sidebar
st.sidebar.header("Filtros")
regiao_options = regiao_data["nome"].unique()
selected_regiao = st.sidebar.multiselect(
    "Selecione a Região Administrativa",
    regiao_options,
    default=regiao_options
)

# Filtro de intervalo de datas para exames
min_date = pd.to_datetime(exame_data["data_exame"]).min().date()
max_date = pd.to_datetime(exame_data["data_exame"]).max().date()
date_range = st.sidebar.date_input(
    "Selecione o intervalo de datas dos exames",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Aplicar filtros
# Filtrar escolas por região
filtered_escola_data = escola_data[escola_data["regiao"].isin(selected_regiao)]

# Filtrar exames por região e data
filtered_alunos = aluno_data[aluno_data["id_escola"].isin(filtered_escola_data["id_escola"])]
filtered_exame_data = exame_data[exame_data["id_aluno"].isin(filtered_alunos["id_aluno"])]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_exame_data = filtered_exame_data[
        (pd.to_datetime(filtered_exame_data["data_exame"]) >= pd.to_datetime(start_date)) & 
        (pd.to_datetime(filtered_exame_data["data_exame"]) <= pd.to_datetime(end_date))
    ]

# Título do Dashboard
st.title("Dashboard Escolar")

# Abas para organizar o conteúdo
tab1, tab2, tab3 = st.tabs(["KPIs e Distribuições", "Mapas e Tendências", "Detalhes"])

# Aba 1: KPIs e Distribuições
with tab1:
    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        total_alunos = filtered_escola_data["total_alunos"].sum()
        st.metric("Total de Alunos", total_alunos)
    with col2:
        total_exames = filtered_exame_data.shape[0]
        st.metric("Total de Exames Realizados", total_exames)
    with col3:
        total_escolas = filtered_escola_data["escola"].nunique()
        st.metric("Total de Escolas", total_escolas)

    # Gráficos de Distribuição
    col4, col5 = st.columns(2)

    with col4:
        # Gráfico de Rosca: Distribuição de Alunos por Região (Top 5)
        top_regioes = filtered_escola_data.groupby("regiao")["total_alunos"].sum().nlargest(5).index
        escola_data_display = filtered_escola_data.copy()
        escola_data_display["regiao_display"] = escola_data_display["regiao"].apply(
            lambda x: x if x in top_regioes else "Outros"
        )
        fig_rosca = px.pie(
            escola_data_display,
            names="regiao_display",
            values="total_alunos",
            title="Distribuição de Alunos por Região (Top 5)",
            hole=0.3,
            color_discrete_sequence=analogous_colors,
            template="plotly_white"
        )
        fig_rosca.update_traces(textinfo='percent+label', pull=[0.1, 0, 0, 0])
        st.plotly_chart(fig_rosca, use_container_width=True)

    with col5:
        # Gráfico de Rosca: Distribuição de Exames por Escola
        exame_por_escola = filtered_exame_data.merge(
            aluno_data[["id_aluno", "id_escola"]], on="id_aluno"
        ).merge(
            filtered_escola_data[["id_escola", "escola"]], on="id_escola"
        )
        exame_count = exame_por_escola.groupby("escola").size().reset_index(name="total_exames")
        fig_rosca_exames = px.pie(
            exame_count,
            names="escola",
            values="total_exames",
            title="Distribuição de Exames por Escola",
            hole=0.3,
            color_discrete_sequence=analogous_colors,
            template="plotly_white"
        )
        fig_rosca_exames.update_traces(textinfo='percent', showlegend=False)
        st.plotly_chart(fig_rosca_exames, use_container_width=True)

# Aba 2: Mapas e Tendências
with tab2:
    # Gráfico de Calor
    st.subheader("Gráfico de Calor - Distrito Federal (Alunos com OD > 4)")
    alunos_od_maior_4 = filtered_exame_data[
        (filtered_exame_data["esferico_od"] > 4) | (filtered_exame_data["cilindrico_od"] > 4)
    ]
    count_alunos_od_maior_4 = alunos_od_maior_4.groupby("aluno").size().reset_index(name="total_exames")
    
    df_df = filtered_escola_data.copy()
    df_df["alunos_com_od_maior_4"] = df_df["escola"].map(
        lambda escola: count_alunos_od_maior_4[count_alunos_od_maior_4["aluno"].isin(
            filtered_alunos[filtered_alunos["id_escola"].isin(
                filtered_escola_data[filtered_escola_data["escola"] == escola]["id_escola"]
            )]["nome"]
        )].shape[0]
    )

    fig_heatmap = go.Figure(go.Scattermapbox(
        lat=df_df["latitude"],
        lon=df_df["longitude"],
        mode='markers',
        marker=dict(
            size=14,
            color=df_df["alunos_com_od_maior_4"],
            colorscale=[[0, '#08306b'], [0.5, '#6baed6'], [1, '#1f77b4']],
            colorbar=dict(title="Alunos com OD > 4"),
        ),
        text=df_df.apply(
            lambda row: f"Escola: {row['escola']}<br>Região: {row['regiao']}<br>Alunos com OD > 4: {row['alunos_com_od_maior_4']}",
            axis=1
        ),
        hoverinfo="text"
    ))
    fig_heatmap.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=8,
        mapbox_center={"lat": -15.7801, "lon": -47.9292},
        title="Calor de Alunos com OD > 4 - Distrito Federal",
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Gráfico de Linhas: Evolução de Exames ao Longo do Tempo
    st.subheader("Evolução de Exames ao Longo do Tempo")
    filtered_exame_data["data_exame"] = pd.to_datetime(filtered_exame_data["data_exame"])
    exames_por_data = filtered_exame_data.groupby(
        filtered_exame_data["data_exame"].dt.to_period("M")
    ).size().reset_index(name="total_exames")
    exames_por_data["data_exame"] = exames_por_data["data_exame"].dt.to_timestamp()

    fig_linha = px.line(
        exames_por_data,
        x="data_exame",
        y="total_exames",
        title="Evolução de Exames Realizados ao Longo do Tempo",
        color_discrete_sequence=analogous_colors,
        template="plotly_white"
    )
    st.plotly_chart(fig_linha, use_container_width=True)

    # Gráfico de Barras: Média de Esférico e Cilíndrico OD por Região
    st.subheader("Média de Esférico e Cilíndrico OD por Região")
    exame_por_regiao = filtered_exame_data.merge(
        aluno_data[["id_aluno", "id_escola"]], on="id_aluno"
    ).merge(
        filtered_escola_data[["id_escola", "regiao"]], on="id_escola"
    )
    media_por_regiao = exame_por_regiao.groupby("regiao")[["esferico_od", "cilindrico_od"]].mean().reset_index()

    fig_barras = go.Figure(data=[
        go.Bar(name="Esférico OD", x=media_por_regiao["regiao"], y=media_por_regiao["esferico_od"], marker_color=analogous_colors[0]),
        go.Bar(name="Cilíndrico OD", x=media_por_regiao["regiao"], y=media_por_regiao["cilindrico_od"], marker_color=analogous_colors[1])
    ])
    fig_barras.update_layout(
        barmode="group",
        title="Média de Esférico e Cilíndrico OD por Região",
        template="plotly_white"
    )
    st.plotly_chart(fig_barras, use_container_width=True)

# Aba 3: Detalhes
with tab3:
    # Tabela de Escolas
    st.subheader("Detalhes das Escolas")
    st.dataframe(
        filtered_escola_data[["escola", "regiao", "total_alunos", "latitude", "longitude"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "escola": "Nome da Escola",
            "regiao": "Região",
            "total_alunos": "Total de Alunos",
            "latitude": "Latitude",
            "longitude": "Longitude"
        }
    )

    # Tabela de Exames com Status
    st.subheader("Dados de Exames")
    filtered_exame_data["status_od"] = filtered_exame_data.apply(
        lambda row: "Crítico" if (row["esferico_od"] > 4 or row["cilindrico_od"] > 4) else "Normal",
        axis=1
    )
    st.dataframe(
        filtered_exame_data[[
            "aluno", "data_exame", "esferico_od", "cilindrico_od", 
            "tamanho_pupila_od", "tamanho_pupila_os", "status_od"
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "aluno": "Nome do Aluno",
            "data_exame": "Data do Exame",
            "esferico_od": "Esférico OD",
            "cilindrico_od": "Cilíndrico OD",
            "tamanho_pupila_od": "Tamanho Pupila OD",
            "tamanho_pupila_os": "Tamanho Pupila OS",
            "status_od": st.column_config.TextColumn("Status OD", help="Indica se o exame apresenta valores críticos")
        }
    )