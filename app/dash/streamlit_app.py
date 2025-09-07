# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import pydeck as pdk
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from streamlit_folium import st_folium
import folium

# --- 0) CONFIGURAÇÕES INICIAIS ---
st.set_page_config(
    page_title="Dashboard Escolar",
    page_icon=":school:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS
st.markdown("""
    <style>
      .stApp { background-color: #f0f2f6; }
      h1, h2, h3 { color: #1f77b4; }
      hr { border: none; border-top: 1px solid #E0E0E0 !important; }
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

# --- 1) CACHE DA ENGINE ---
if hasattr(st, "cache_resource"):
    cache_engine = st.cache_resource
else:
    cache_engine = lambda f: st.cache(allow_output_mutation=True)(f)

@cache_engine
def get_engine():
    return create_engine(
        "postgresql://meu_usuario:minha_senha@localhost:5432/postgres",
        pool_size=5,
        max_overflow=10
    )

# --- 2) FUNÇÃO DE CARREGAMENTO ---
@st.cache_data(ttl=600)
def load_data(sql: str, params=None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

# --- 3) CARREGAR DADOS ---
regiao_data = load_data("""
    SELECT DISTINCT regiao_administrativa AS regiao
    FROM escola;
""")
aluno_data = load_data("""
    SELECT id_aluno, nome, data_nascimento, sexo, id_escola, regiao_administrativa
    FROM aluno;
""")
escola_data = load_data("""
    SELECT e.id_escola, e.nome AS escola, e.regiao_administrativa AS regiao,
           COUNT(a.id_aluno) AS total_alunos, e.latitude, e.longitude
    FROM escola e
    LEFT JOIN aluno a ON a.id_escola = e.id_escola
    GROUP BY e.id_escola, e.nome, e.regiao_administrativa, e.latitude, e.longitude;
""")
escola_data["total_alunos"] = (
    pd.to_numeric(escola_data["total_alunos"], errors="coerce").fillna(0).astype(int)
)
exame_data = load_data("""
    SELECT x.id_exame, x.id_aluno, a.nome AS aluno,
           x.data_hora_escaneamento AS data_exame,
           x.se_direito    AS esferico_od,
           x.ds_direito    AS cilindrico_od,
           x.se_esquerdo   AS esferico_os,
           x.ds_esquerdo   AS cilindrico_os
    FROM exame x
    JOIN aluno a ON x.id_aluno = a.id_aluno;
""")

# --- 4) PALETA DE CORES ---
palette = ['#19D3F3', '#00CC96', '#EF553B', '#AB63FA', '#FFA15A']

# --- 4) SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros")

# 4.1) Filtrar por Região Administrativa
regioes = regiao_data["regiao"].unique()
selecionadas = st.sidebar.multiselect(
    "Região Administrativa", options=regioes, default=list(regioes)
)

# 4.2) Filtrar por Escola (após selecionar regiões)
escolas = escola_data[escola_data["regiao"].isin(selecionadas)]["escola"].unique()
selecionadas_escolas = st.sidebar.multiselect(
    "Escola",
    options=escolas,
    default=list(escolas)
)

# 4.3) Filtrar por intervalo de datas de exame
exame_data["data_exame"] = pd.to_datetime(exame_data["data_exame"])
min_date = exame_data["data_exame"].dt.date.min()
max_date = exame_data["data_exame"].dt.date.max()
date_range = st.sidebar.date_input(
    "Intervalo de Datas de Exame",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# --- 5) APLICAR FILTROS ---
# Filtra escolas por região e escola
f_escolas = escola_data[
    escola_data["regiao"].isin(selecionadas) &
    escola_data["escola"].isin(selecionadas_escolas)
]
# Filtra alunos dessas escolas
f_alunos = aluno_data[aluno_data["id_escola"].isin(f_escolas["id_escola"])]
# Filtra exames desses alunos
f_exames = exame_data[exame_data["id_aluno"].isin(f_alunos["id_aluno"])]
# Filtra por data de exame
if len(date_range) == 2:
    sd, ed = date_range
    f_exames = f_exames[
        (f_exames["data_exame"].dt.date >= sd) &
        (f_exames["data_exame"].dt.date <= ed)
    ]

# --- 7) TÍTULO E ABAS ---
st.title("Dashboard Escolar")
tab1, tab2, tab3 = st.tabs(["KPIs e Distribuições", "Mapas e Tendências", "Detalhes"])

# === Aba 1: KPIs e Distribuições (REFEITA com totals) ===
with tab1:
    engine = get_engine()

    # Carrega flags persistidas (defensivo se não existirem)
    try:
        saved1 = pd.read_sql("SELECT aluno, exame_feito FROM alunos_criticos", engine)
    except:
        saved1 = pd.DataFrame(columns=["aluno", "exame_feito"])
    try:
        saved2 = pd.read_sql(
            "SELECT aluno, necessidade_oculos, outras_patologias FROM alunos_necessitam_oculos",
            engine
        )
    except:
        saved2 = pd.DataFrame(columns=["aluno", "necessidade_oculos", "outras_patologias"])
    try:
        saved3 = pd.read_sql("SELECT aluno, oculos_entregue FROM alunos_oculos_entregue", engine)
    except:
        saved3 = pd.DataFrame(columns=["aluno", "oculos_entregue"])

    # ---------- Base única que cruza aluno→(data, escola, região) e flags ----------
    # Considera a 1ª data de exame por aluno para séries e agregações temporais
    first_exam = (
        f_exames.sort_values("data_exame")
        .groupby("aluno", as_index=False)
        .first()[["aluno", "data_exame", "id_aluno"]]
    )
    alu_escola = f_alunos[["id_aluno", "id_escola"]]
    esc_cols = f_escolas[["id_escola", "escola", "regiao"]]

    base = (first_exam
            .merge(alu_escola, on="id_aluno", how="left")
            .merge(esc_cols, on="id_escola", how="left"))

    # Anexa flags (preenche False)
    base = (base
            .merge(saved1, on="aluno", how="left")
            .merge(saved2, on="aluno", how="left")
            .merge(saved3, on="aluno", how="left"))
    for col in ["exame_feito", "necessidade_oculos", "outras_patologias", "oculos_entregue"]:
        if col not in base:
            base[col] = False
        base[col] = base[col].fillna(False).astype(bool)

    # ---------- Totais solicitados ----------
    total_alunos = int(pd.to_numeric(f_escolas["total_alunos"], errors="coerce").fillna(0).sum())
    total_escolas = int(f_escolas["escola"].nunique())
    alunos_triados_unicos = int(f_exames["id_aluno"].nunique())  # alunos distintos com triagem

    # Indicadas p/ exame (status crítico) a partir dos exames filtrados atuais
    n_indicadas = int(
        (f_exames.assign(
            status_od=lambda df: df.apply(
                lambda r: "Crítico"
                if (r["esferico_od"] > 4 or r["cilindrico_od"] > 4)
                else "Normal",
                axis=1
            )
        )
        .query("status_od == 'Crítico'")
        ["aluno"].nunique())
    )

    # Demais contagens das flags persistidas
    n_examinadas = int(base["exame_feito"].sum())
    n_oculos     = int(base["necessidade_oculos"].sum())
    n_patol      = int(base["outras_patologias"].sum())
    n_entregues  = int(base["oculos_entregue"].sum())

    # ---------- KPIs topo (linha 1: Totais) ----------
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Alunos", total_alunos)
    c2.metric("Alunos Triados (únicos)", alunos_triados_unicos)
    c3.metric("Total de Escolas", total_escolas)

    # ---------- KPIs topo (linha 2: Jornada) ----------
    c4, c5, c6, c7, c8 = st.columns(5)
    c4.metric("Indicadas p/ Exame", n_indicadas)
    c5.metric("Examinadas", n_examinadas)
    c6.metric("Necessitam Óculos", n_oculos)
    c7.metric("Outras Patologias", n_patol)
    c8.metric("Óculos Entregues", n_entregues)

    # Taxas de conversão (defensivo com denominador mínimo 1)
    def ratio(num, den):
        den = max(int(den), 1)
        return f"{(num/den)*100:.1f}%"
    st.caption(
        f"**Conversões:** Examinadas/Indicadas: {ratio(n_examinadas, n_indicadas)} • "
        f"Necessitam/Examinadas: {ratio(n_oculos, n_examinadas)} • "
        f"Entregues/Necessitam: {ratio(n_entregues, n_oculos)}"
    )

    st.divider()

    # ---------- Funil da Jornada ----------
    funnel_labels = ["Indicadas", "Examinadas", "Necessitam Óculos", "Óculos Entregues"]
    funnel_vals   = [n_indicadas, n_examinadas, n_oculos, n_entregues]
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_labels,
        x=funnel_vals,
        textinfo="value+percent previous",
        marker=dict(color=palette + palette)
    ))
    fig_funnel.update_layout(
        title="Funil: Triagem → Exame → Necessidade → Entrega",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=20)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    st.divider()

    # ---------- Stack por Região (Examinadas, Necessitam, Entregues) ----------
    reg_agg = (base.groupby("regiao", dropna=False)
               .agg(examinadas=("exame_feito", "sum"),
                    necessidade=("necessidade_oculos", "sum"),
                    entregues=("oculos_entregue", "sum"))
               .reset_index()
               .fillna({"regiao": "Sem Região"}))
    fig_stack = go.Figure()
    fig_stack.add_bar(name="Examinadas", x=reg_agg["regiao"], y=reg_agg["examinadas"])
    fig_stack.add_bar(name="Necessitam Óculos", x=reg_agg["regiao"], y=reg_agg["necessidade"])
    fig_stack.add_bar(name="Entregues", x=reg_agg["regiao"], y=reg_agg["entregues"])
    fig_stack.update_layout(
        barmode="stack",
        title="Status por Região Administrativa",
        template="plotly_white",
        xaxis_title="Região",
        yaxis_title="Total"
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    st.divider()

    # ---------- Ranking por Escola: Taxa de Entrega (entre os que precisam) ----------
    esc_need = (base.groupby(["escola"], dropna=False)
                .agg(necessitam=("necessidade_oculos", "sum"),
                     entregues=("oculos_entregue", "sum"))
                .reset_index())
    esc_need["taxa_entrega"] = esc_need.apply(
        lambda r: (r["entregues"]/r["necessitam"])*100 if r["necessitam"] > 0 else 0.0, axis=1
    )
    esc_rank = esc_need.sort_values("taxa_entrega", ascending=False).head(20)
    fig_rank = px.bar(
        esc_rank,
        x="taxa_entrega",
        y="escola",
        orientation="h",
        text=esc_rank["taxa_entrega"].map(lambda v: f"{v:.1f}%"),
        title="Top 20 Escolas por Taxa de Entrega (entre os que necessitam)",
        labels={"taxa_entrega": "Taxa de Entrega (%)", "escola": "Escola"},
        color="escola",
        color_discrete_sequence=palette,
        template="plotly_white"
    )
    fig_rank.update_traces(textposition="outside")
    fig_rank.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_rank, use_container_width=True)

    st.divider()

    # ---------- Séries temporais por etapa ----------
    def monthly_count(df, flag_col):
        tmp = df[df[flag_col]].copy()
        if tmp.empty:
            return pd.DataFrame({"mes": [], "qtde": []})
        tmp["mes"] = pd.to_datetime(tmp["data_exame"]).dt.to_period("M").dt.to_timestamp()
        return tmp.groupby("mes", as_index=False).size().rename(columns={"size": "qtde"})

    serie_exam  = monthly_count(base, "exame_feito")
    serie_need  = monthly_count(base, "necessidade_oculos")
    serie_deliv = monthly_count(base, "oculos_entregue")

    fig_series = go.Figure()
    fig_series.add_trace(go.Scatter(
        x=serie_exam["mes"], y=serie_exam["qtde"], mode="lines+markers", name="Examinadas"
    ))
    fig_series.add_trace(go.Scatter(
        x=serie_need["mes"], y=serie_need["qtde"], mode="lines+markers", name="Necessitam Óculos"
    ))
    fig_series.add_trace(go.Scatter(
        x=serie_deliv["mes"], y=serie_deliv["qtde"], mode="lines+markers", name="Entregues"
    ))
    fig_series.update_layout(
        title="Evolução Mensal por Etapa",
        template="plotly_white",
        xaxis_title="Mês",
        yaxis_title="Quantidade"
    )
    st.plotly_chart(fig_series, use_container_width=True)

    st.divider()

    # ---------- Donut entre examinados: Necessitam vs Outras Patologias ----------
    base_exam = base[base["exame_feito"]].copy()
    donut_vals = [
        int(base_exam["necessidade_oculos"].sum()),
        int(base_exam["outras_patologias"].sum())
    ]
    donut_labels = ["Necessitam Óculos", "Outras Patologias"]
    fig_donut = px.pie(
        names=donut_labels,
        values=donut_vals,
        hole=0.5,
        color_discrete_sequence=palette,
        title="Distribuição entre Examinados",
        template="plotly_white"
    )
    fig_donut.update_traces(textinfo="label+percent")
    st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # ---------- Gráficos originais úteis ----------
    # Alunos por Região (Top 5)
    top5 = f_escolas.groupby("regiao")["total_alunos"].sum().nlargest(5).index
    tmp = f_escolas.copy()
    tmp["regiao_disp"] = tmp["regiao"].where(tmp["regiao"].isin(top5), "Outros")
    fig1 = px.pie(
        tmp,
        names="regiao_disp",
        values="total_alunos",
        hole=0.3,
        color_discrete_sequence=palette,
        title="Alunos por Região (Top 5)",
        template="plotly_white"
    )
    fig1.update_traces(textinfo="percent+label", pull=[0.1] + [0] * 4)
    st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # Exames por Escola
    if not f_exames.empty:
        ee = (
            f_exames
            .merge(f_alunos[["id_aluno", "id_escola"]], on="id_aluno")
            .merge(f_escolas[["id_escola", "escola"]], on="id_escola")
        )
        cnt = ee.groupby("escola")["id_exame"].count().reset_index(name="total_exames")
        cnt = cnt.sort_values("total_exames", ascending=True)
        total = cnt["total_exames"].sum()
        cnt["percent_str"] = (cnt["total_exames"] / max(total, 1) * 100).round(1).astype(str) + "%"
        fig2 = px.bar(
            cnt,
            x="total_exames",
            y="escola",
            orientation="h",
            text="percent_str",
            labels={"total_exames": "Total de Exames"},
            color="escola",
            color_discrete_sequence=palette,
            title="Exames por Escola",
            template="plotly_white"
        )
        fig2.update_traces(textposition="outside", textfont=dict(size=12))
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

# === Aba 2: Mapas e Tendências ===
with tab2:
    st.subheader("Mapa de Exames por Região Administrativa")

    # 1) Agrega total de exames por RA
    region_counts = (
        f_exames
        .merge(f_alunos[['id_aluno','id_escola']], on='id_aluno')
        .merge(f_escolas[['id_escola','regiao']], on='id_escola')
        .groupby('regiao')
        .size()
        .reset_index(name='total_exames')
    )

    # 2) Carrega GeoJSON completo e filtra só as RAs necessárias
    import json
    with open('regions.geojson', 'r', encoding='utf-8') as f:
        gj = json.load(f)

    nomes = set(region_counts['regiao'])
    gj['features'] = [
        feat for feat in gj['features']
        if feat['properties']['ra'] in nomes
    ]

    # 3) Plota o choropleth
    df_lat = f_escolas['latitude'].mean()
    df_lon = f_escolas['longitude'].mean()

    fig = px.choropleth_mapbox(
        region_counts,
        geojson=gj,
        locations='regiao',
        featureidkey='properties.ra',
        color='total_exames',
        color_continuous_scale=[
            "#FEB24C",  # amarelo-alaranjado
            "#FD8D3C",  # laranja
            "#E31A1C"   # vermelho-fogo
        ],
        range_color=(region_counts['total_exames'].min(), region_counts['total_exames'].max()),
        mapbox_style='carto-positron',
        zoom=9,
        center={'lat': df_lat, 'lon': df_lon},
        opacity=0.7,
        labels={'total_exames':'# Exames'}
    )

    fig.update_traces(
        marker_line_width=0.5,
        marker_line_color='white'
    )
    fig.update_layout(margin={'r':0,'t':0,'l':0,'b':0})

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Evolução Mensal de Exames")
    serie = (
        f_exames
        .groupby(f_exames['data_exame'].dt.to_period('M'))
        .size()
        .reset_index(name='qtde')
    )
    serie['data_exame'] = serie['data_exame'].dt.to_timestamp()
    fig_ln = px.line(
        serie, x='data_exame', y='qtde',
        title='Exames por Mês', template='plotly_white',
        color_discrete_sequence=palette
    )
    st.plotly_chart(fig_ln, use_container_width=True)

    st.divider()

    st.subheader("Média de Esférico/Cilíndrico por Região")
    mr = (
        f_exames
        .merge(f_alunos[['id_aluno','id_escola']], on='id_aluno')
        .merge(f_escolas[['id_escola','regiao']], on='id_escola')
        .groupby('regiao')[['esferico_od','cilindrico_od']]
        .mean().reset_index()
    )
    fig_bar = go.Figure([
        go.Bar(name='Esférico OD', x=mr['regiao'], y=mr['esferico_od'], marker_color=palette[0]),
        go.Bar(name='Cilíndrico OD', x=mr['regiao'], y=mr['cilindrico_od'], marker_color=palette[1])
    ])
    fig_bar.update_layout(
        barmode='group',
        title='Média Esférico/Cilíndrico por Região',
        template='plotly_white'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# === Aba 3: Detalhes (TODAS TABELAS EDITÁVEIS) ===
with tab3:
    st.subheader("Alunos Triados")

    engine = get_engine()

    # --- 0) Carregar flags existentes do banco ---
    try:
        saved1 = pd.read_sql("SELECT aluno, exame_feito FROM alunos_criticos", engine)
    except:
        saved1 = pd.DataFrame(columns=["aluno", "exame_feito"])

    try:
        saved2 = pd.read_sql(
            "SELECT aluno, necessidade_oculos, outras_patologias "
            "FROM alunos_necessitam_oculos", engine
        )
    except:
        saved2 = pd.DataFrame(columns=["aluno", "necessidade_oculos", "outras_patologias"])

    try:
        saved3 = pd.read_sql(
            "SELECT aluno, oculos_entregue FROM alunos_oculos_entregue", engine
        )
    except:
        saved3 = pd.DataFrame(columns=["aluno", "oculos_entregue"])

    # --- 1) Marcar exame feito (EDITÁVEL) ---
    f_exames = f_exames.copy()
    f_exames["status_od"] = f_exames.apply(
        lambda r: "Crítico"
        if (r["esferico_od"] > 4 or r["cilindrico_od"] > 4)
        else "Normal",
        axis=1
    )
    df1 = f_exames.loc[
        f_exames["status_od"] == "Crítico",
        ["aluno", "data_exame", "esferico_od", "cilindrico_od"]
    ].copy()

    mapa_exame_feito = saved1.set_index("aluno")["exame_feito"] if not saved1.empty else pd.Series(dtype=bool)
    df1["exame_feito"] = df1["aluno"].map(mapa_exame_feito).fillna(False).astype(bool)

    gb1 = GridOptionsBuilder.from_dataframe(df1)
    gb1.configure_default_column(editable=False)
    gb1.configure_column(
        "exame_feito",
        header_name="Exame Feito?",
        editable=True,
        cellEditor="agCheckboxCellEditor",
        type=["booleanColumn"]
    )
    grid1 = AgGrid(
        df1,
        gridOptions=gb1.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        height=300,
        key="grid1"
    )
    df1 = pd.DataFrame(grid1["data"])
    df1["exame_feito"] = df1["exame_feito"].astype(bool)

    st.divider()
    st.subheader("Alunos que fizeram o exame")

    # --- 2) Necessita óculos & outras patologias (EDITÁVEIS) ---
    df2 = df1[df1["exame_feito"]].copy()

    mapa_nec = saved2.set_index("aluno")["necessidade_oculos"] if ("aluno" in saved2 and "necessidade_oculos" in saved2) and not saved2.empty else pd.Series(dtype=bool)
    mapa_op  = saved2.set_index("aluno")["outras_patologias"] if ("aluno" in saved2 and "outras_patologias" in saved2) and not saved2.empty else pd.Series(dtype=bool)

    df2["necessidade_oculos"] = df2["aluno"].map(mapa_nec).fillna(False).astype(bool)
    df2["outras_patologias"]  = df2["aluno"].map(mapa_op).fillna(False).astype(bool)

    gb2 = GridOptionsBuilder.from_dataframe(df2)
    gb2.configure_default_column(editable=False)
    gb2.configure_column(
        "necessidade_oculos",
        header_name="Necessita Óculos?",
        editable=True,
        cellEditor="agCheckboxCellEditor",
        type=["booleanColumn"]
    )
    gb2.configure_column(
        "outras_patologias",
        header_name="Outras Patologias?",
        editable=True,
        cellEditor="agCheckboxCellEditor",
        type=["booleanColumn"]
    )
    grid2 = AgGrid(
        df2,
        gridOptions=gb2.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        height=300,
        key="grid2"
    )
    df2 = pd.DataFrame(grid2["data"])
    df2["necessidade_oculos"] = df2["necessidade_oculos"].astype(bool)
    df2["outras_patologias"]  = df2["outras_patologias"].astype(bool)

    # --- 2.1) Visão filtrada: Alunos com outras patologias (EDITÁVEL) ---
    st.divider()
    st.subheader("Alunos com outras patologias")

    df_op_view = df2[df2["outras_patologias"]].copy()
    cols_op = ["aluno", "data_exame", "outras_patologias"]
    gb_op = GridOptionsBuilder.from_dataframe(df_op_view[cols_op])
    gb_op.configure_default_column(editable=False)
    gb_op.configure_column(
        "outras_patologias",
        header_name="Outras Patologias?",
        editable=True,
        cellEditor="agCheckboxCellEditor",
        type=["booleanColumn"]
    )
    grid_op = AgGrid(
        df_op_view[cols_op],
        gridOptions=gb_op.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        height=300,
        key="grid_op"
    )
    df_op_atual = pd.DataFrame(grid_op["data"])
    if not df_op_atual.empty:
        mapa_op_atual = df_op_atual.set_index("aluno")["outras_patologias"].astype(bool)
        sel = df2["aluno"].isin(mapa_op_atual.index)
        df2.loc[sel, "outras_patologias"] = df2.loc[sel, "aluno"].map(mapa_op_atual)

    # --- 3) Necessitam óculos + Marcar óculos entregues (EDITÁVEL) ---
    st.divider()
    st.subheader("Alunos que necessitam de óculos")

    df3 = df2[df2["necessidade_oculos"]].copy()

    mapa_entregue = saved3.set_index("aluno")["oculos_entregue"] if not saved3.empty else pd.Series(dtype=bool)
    df3["oculos_entregue"] = df3["aluno"].map(mapa_entregue).fillna(False).astype(bool)

    gb3 = GridOptionsBuilder.from_dataframe(df3)
    gb3.configure_default_column(editable=False)
    gb3.configure_column(
        "oculos_entregue",
        header_name="Óculos Entregue?",
        editable=True,
        cellEditor="agCheckboxCellEditor",
        type=["booleanColumn"]
    )
    grid3 = AgGrid(
        df3,
        gridOptions=gb3.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        height=300,
        key="grid3"
    )
    df3 = pd.DataFrame(grid3["data"])
    df3["oculos_entregue"] = df3["oculos_entregue"].astype(bool)

    # --- 3.1) Visão filtrada: Já receberam óculos (EDITÁVEL) ---
    st.divider()
    st.subheader("Alunos que já receberam óculos")

    df4 = df3[df3["oculos_entregue"]].copy()
    cols_df4 = ["aluno", "data_exame", "esferico_od", "cilindrico_od", "oculos_entregue"]

    gb4 = GridOptionsBuilder.from_dataframe(df4[cols_df4])
    gb4.configure_default_column(editable=False)
    gb4.configure_column(
        "oculos_entregue",
        header_name="Óculos Entregue?",
        editable=True,
        cellEditor="agCheckboxCellEditor",
        type=["booleanColumn"]
    )
    grid4 = AgGrid(
        df4[cols_df4],
        gridOptions=gb4.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        height=300,
        key="grid4"
    )
    df4_atual = pd.DataFrame(grid4["data"])
    if not df4_atual.empty:
        mapa_ent_atual = df4_atual.set_index("aluno")["oculos_entregue"].astype(bool)
        sel3 = df3["aluno"].isin(mapa_ent_atual.index)
        df3.loc[sel3, "oculos_entregue"] = df3.loc[sel3, "aluno"].map(mapa_ent_atual)

    st.divider()
    if st.button("Salvar"):
        # df1: exame_feito
        df1[["aluno", "exame_feito"]].to_sql(
            "alunos_criticos", engine, if_exists="replace", index=False
        )
        # df2: necessidade_oculos, outras_patologias
        df2[["aluno", "necessidade_oculos", "outras_patologias"]].to_sql(
            "alunos_necessitam_oculos", engine, if_exists="replace", index=False
        )
        # df3: oculos_entregue
        df3[["aluno", "oculos_entregue"]].to_sql(
            "alunos_oculos_entregue", engine, if_exists="replace", index=False
        )
        st.success("Dados sincronizados com sucesso!")
