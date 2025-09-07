# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

# Importações para Pydeck
import pydeck as pdk

# --- 0) CONFIGURAÇÕES INICIAIS ---
st.set_page_config(
    page_title="Dashboard Escolar",
    page_icon=":school:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para restaurar divisores horizontais e verticais
st.markdown("""
    <style>
      .stApp { background-color: #f0f2f6; }
      h1, h2, h3 { color: #1f77b4; }
      /* todos os <hr> e st.divider() ficam com linha cinza clara */
      hr {
        border: none;
        border-top: 1px solid #E0E0E0 !important;
      }
      /* bordas verticais entre colunas de métricas */
      [data-testid="metric-container"] {
        border-right: 1px solid #E0E0E0;
        padding-right: 1rem;
        margin-right: 1rem;
      }
      [data-testid="metric-container"]:last-child {
        border-right: none;
      }
    </style>
""", unsafe_allow_html=True)

# --- 1) CACHE DA ENGINE (singleton/fallback) ---
if hasattr(st, "cache_resource"):
    cache_engine = st.cache_resource
else:
    cache_engine = lambda f: st.cache(allow_output_mutation=True)(f)

@cache_engine
def get_engine():
    """
    Cria e retorna a SQLAlchemy Engine.
    Ajuste a string abaixo conforme seu host/porta/databse/usuário/senha.
    """
    return create_engine(
        "postgresql://meu_usuario:minha_senha@192.168.0.28:5432/postgres",
        pool_size=5,
        max_overflow=10
    )

# --- 2) FUNÇÃO DE CARREGAMENTO COM CACHE ---
@st.cache_data(ttl=600)
def load_data(sql: str, params=None) -> pd.DataFrame:
    """
    Executa a SQL e retorna um DataFrame. Cache de 10 minutos.
    """
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

# --- 3) CARREGAR TODOS OS DADOS COM BASE NA NOVA MODELAGEM ---

# 3.1) Regiões (únicas) vindas da tabela 'escola'
regiao_data = load_data("""
    SELECT DISTINCT regiao_administrativa AS regiao
    FROM escola;
""")

# 3.2) Alunos
aluno_data = load_data("""
    SELECT
      id_aluno,
      nome,
      data_nascimento,
      sexo,
      id_escola,
      regiao_administrativa
    FROM aluno;
""")

# 3.3) Escolas, com contagem de alunos e coordenadas
escola_data = load_data("""
    SELECT
      e.id_escola,
      e.nome AS escola,
      e.regiao_administrativa AS regiao,
      COUNT(a.id_aluno) AS total_alunos,
      e.latitude,
      e.longitude
    FROM escola e
    LEFT JOIN aluno a ON a.id_escola = e.id_escola
    GROUP BY
      e.id_escola,
      e.nome,
      e.regiao_administrativa,
      e.latitude,
      e.longitude;
""")
escola_data["total_alunos"] = (
    pd.to_numeric(escola_data["total_alunos"], errors="coerce")
      .fillna(0)
      .astype(int)
)

# 3.4) Exames (mapeamento de campos conforme nova modelagem)
exame_data = load_data("""
    SELECT
      x.id_exame,
      x.id_aluno,
      a.nome AS aluno,
      x.data_hora_escaneamento AS data_exame,
      x.se_direito    AS esferico_od,
      x.ds_direito    AS cilindrico_od,
      x.se_esquerdo   AS esferico_os,
      x.ds_esquerdo   AS cilindrico_os
    FROM exame x
    JOIN aluno a ON x.id_aluno = a.id_aluno;
""")

# --- 4) PALETA DE CORES E OUTRAS VARIÁVEIS GLOBAIS ---
analogous_colors = ['#1f77b4', '#4a90e2', '#2a5d8e', '#6baed6', '#08306b']

# --- 5) SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros")

# 5.1) Filtrar por Região Administrativa
regioes = regiao_data["regiao"].unique()
selecionadas = st.sidebar.multiselect(
    "Região Administrativa",
    options=regioes,
    default=list(regioes)
)

# 5.2) Filtrar por intervalo de datas de exame
exame_data["data_exame"] = pd.to_datetime(exame_data["data_exame"])
min_date = exame_data["data_exame"].dt.date.min()
max_date = exame_data["data_exame"].dt.date.max()
date_range = st.sidebar.date_input(
    "Intervalo de Datas de Exame",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# --- 6) APLICAR FILTROS AOS DADOS ---

# Filtra escolas pela(s) região(ões) selecionada(s)
f_escolas = escola_data[escola_data["regiao"].isin(selecionadas)]
# Filtra alunos cujas escolas estão em f_escolas
f_alunos = aluno_data[aluno_data["id_escola"].isin(f_escolas["id_escola"])]
# Filtra exames cujos alunos pertencem a f_alunos
f_exames = exame_data[exame_data["id_aluno"].isin(f_alunos["id_aluno"])]

# Filtra por data de exame, se o usuário selecionou um intervalo
if len(date_range) == 2:
    sd, ed = date_range
    f_exames = f_exames[
        (f_exames["data_exame"].dt.date >= sd) &
        (f_exames["data_exame"].dt.date <= ed)
    ]

# --- 7) TÍTULO E ABAS PRINCIPAIS ---
st.title("Dashboard Escolar")
tab1, tab2, tab3 = st.tabs(["KPIs e Distribuições", "Mapas e Tendências", "Detalhes"])

# === Aba 1: KPIs e Distribuições ===
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Alunos", int(f_escolas["total_alunos"].sum()))
    c2.metric("Total de Exames", f_exames.shape[0])
    c3.metric("Total de Escolas", f_escolas["escola"].nunique())

    st.divider()

    # Rosca: Alunos por Região (Top 5)
    top5 = f_escolas.groupby("regiao")["total_alunos"].sum().nlargest(5).index
    tmp = f_escolas.copy()
    tmp["regiao_disp"] = tmp["regiao"].where(tmp["regiao"].isin(top5), "Outros")
    fig1 = px.pie(
        tmp,
        names="regiao_disp",
        values="total_alunos",
        hole=0.3,
        color_discrete_sequence=analogous_colors,
        title="Alunos por Região (Top 5)",
        template="plotly_white"
    )
    fig1.update_traces(textinfo="percent+label", pull=[0.1] + [0] * 4)
    st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # Gráfico de Barras: Exames por Escola (horizontal, com percentuais)
    ee = (
        f_exames
        .merge(f_alunos[["id_aluno", "id_escola"]], on="id_aluno")
        .merge(f_escolas[["id_escola", "escola"]], on="id_escola")
    )
    cnt = ee.groupby("escola")["id_exame"].count().reset_index(name="total_exames")

    # Ordena pela quantidade de exames (do maior para o menor)
    cnt = cnt.sort_values("total_exames", ascending=True)

    # Calcula percentual
    total_geral = cnt["total_exames"].sum()
    cnt["percent"] = (cnt["total_exames"] / total_geral * 100).round(1).astype(str) + "%"

    fig2 = px.bar(
        cnt,
        x="total_exames",
        y="escola",
        orientation="h",
        text="percent",  # exibe o % ao final de cada barra
        labels={"total_exames": "Total de Exames", "escola": "Escola"},
        color="total_exames",
        color_continuous_scale="Blues",
        title="Exames por Escola",
        template="plotly_white"
    )

    fig2.update_traces(
        textposition="outside",       # percentual aparece fora da barra
        textfont=dict(size=12, color="#444444")
    )
    fig2.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=200, r=40, t=40, b=40),  # espaço extra à esquerda para nomes longos
        coloraxis_showscale=False  # esconde barra de cores
    )

    st.plotly_chart(fig2, use_container_width=True)

# === Aba 2: Mapas e Tendências ===
with tab2:
    st.subheader("Mapa de Alunos com OD > 4 (Pydeck)")

    # Critério de OD crítico: esferico_od ou cilindrico_od > 4
    od4 = f_exames[
        (f_exames["esferico_od"] > 4) |
        (f_exames["cilindrico_od"] > 4)
    ]
    od4_cnt = od4.groupby("aluno").size().reset_index(name="qtde")

    # Prepara DataFrame para o mapa: cada escola, conta quantos alunos críticos
    dfm = f_escolas.copy()
    def conta_criticos_por_escola(row):
        alunos_da_escola = f_alunos[
            f_alunos["id_escola"] == row["id_escola"]
        ]["nome"]
        return od4_cnt[od4_cnt["aluno"].isin(alunos_da_escola)].shape[0]

    dfm["criticos"] = dfm.apply(conta_criticos_por_escola, axis=1)

    # Se não houver latitude/longitude, filtra
    dfm = dfm.dropna(subset=["latitude", "longitude"])

    # Cria coluna 'radius' e 'color' para Pydeck:
    # - radius: maior para mais críticos (multiplicado por 200 metros)
    # - color: mapeia criticos→tonalidade de vermelho (quanto maior, mais vermelho)
    dfm["radius"] = (dfm["criticos"] ** 0.5) * 200 + 100
    # cor em RGB: [verm, verde, azul], verm proporcional a criticos
    maxc = dfm["criticos"].max() if dfm["criticos"].max() > 0 else 1
    dfm["color"] = dfm["criticos"].apply(
        lambda c: [
            int(255 * (c / maxc)),         # componente vermelho
            int(255 * (1 - c / maxc)),     # componente verde
            100                             # componente azul fixo para contraste
        ]
    )

    # Define camada Pydeck
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=dfm,
        get_position=["longitude", "latitude"],
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
        auto_highlight=True
    )

    # Estado inicial de visualização  (centra no DF)
    if not dfm.empty:
        view_state = pdk.ViewState(
            latitude=dfm["latitude"].mean(),
            longitude=dfm["longitude"].mean(),
            zoom=8,
            pitch=0
        )
    else:
        view_state = pdk.ViewState(latitude=-15.78, longitude=-47.92, zoom=8, pitch=0)

    # Tooltip ao passar o mouse
    tooltip = {
        "html": "<b>Escola:</b> {escola} <br/>"
                "<b>Região:</b> {regiao} <br/>"
                "<b>Críticos:</b> {criticos}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    # Monta o deck.gl e exibe
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    )
    st.pydeck_chart(r)

    st.divider()

    st.subheader("Evolução Mensal de Exames")
    serie = (
        f_exames
        .groupby(f_exames["data_exame"].dt.to_period("M"))
        .size()
        .reset_index(name="qtde")
    )
    serie["data_exame"] = serie["data_exame"].dt.to_timestamp()
    fig_ln = px.line(
        serie,
        x="data_exame",
        y="qtde",
        title="Exames por Mês",
        template="plotly_white",
        color_discrete_sequence=analogous_colors
    )
    st.plotly_chart(fig_ln, use_container_width=True)

    st.divider()

    st.subheader("Média de Esférico/Cilíndrico por Região")
    mr = (
        f_exames
        .merge(f_alunos[["id_aluno", "id_escola"]], on="id_aluno")
        .merge(f_escolas[["id_escola", "regiao"]], on="id_escola")
        .groupby("regiao")[["esferico_od", "cilindrico_od"]]
        .mean()
        .reset_index()
    )
    fig_bar = go.Figure([
        go.Bar(name="Esférico OD", x=mr["regiao"], y=mr["esferico_od"]),
        go.Bar(name="Cilíndrico OD", x=mr["regiao"], y=mr["cilindrico_od"])
    ])
    fig_bar.update_layout(
        barmode="group",
        title="Média Esférico/Cilíndrico por Região",
        template="plotly_white"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# === Aba 3: Detalhes ===
with tab3:
    st.subheader("Detalhes das Escolas")
    st.dataframe(
        f_escolas[["escola", "regiao", "total_alunos", "latitude", "longitude"]],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("Detalhes de Exames")
    f_exames["status_od"] = f_exames.apply(
        lambda r: "Crítico" if (r["esferico_od"] > 4 or r["cilindrico_od"] > 4) else "Normal",
        axis=1
    )
    st.dataframe(
        f_exames[[
            "aluno",
            "data_exame",
            "esferico_od",
            "cilindrico_od",
            "esferico_os",
            "cilindrico_os",
            "status_od"
        ]],
        use_container_width=True,
        hide_index=True
    )
