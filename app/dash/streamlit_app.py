import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000/api/data")
response = requests.get(API_URL)

# Obtenção de dados da API
response = requests.get(API_URL)
if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)
else:
    st.error("Erro ao obter dados da API Flask.")
    df = pd.DataFrame()

# Mapa interativo
if not df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[longitude, latitude]",
        get_radius=10000,
        get_fill_color="[200, 30, 0, 160]",
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=df["latitude"].mean(),
        longitude=df["longitude"].mean(),
        zoom=4,
        pitch=50
    )

    tooltip = {"html": "<b>Região:</b> {region}<br><b>Valor:</b> {value}"}

    deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)

    st.pydeck_chart(deck)

else:
    st.warning("Nenhum dado para exibir.")

st.title("Dashboard com Flask e Streamlit")
st.write("Dados consumidos diretamente da API Flask.")

