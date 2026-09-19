"""
App Streamlit — Analytics em Saúde Pública: Mortalidade no Brasil (DATASUS/SIM)
Categoria piloto: Mortalidade Geral

Rodar com: streamlit run app.py
"""
import glob
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.io.leitura_tabnet import ler_arquivo_tabnet

st.set_page_config(page_title="Mortalidade no Brasil (SIM)", layout="wide")

PASTA_DADOS = Path("data/raw/datasus_sim/mortalidade_geral")


@st.cache_data
def carregar_todos_os_arquivos():
    """Lê os 45 arquivos uma única vez e guarda em cache (evita reprocessar
    a cada interação do usuário no app)."""
    arquivos = sorted(glob.glob(str(PASTA_DADOS / "*.csv")))
    dfs = []
    for caminho in arquivos:
        df, _, _ = ler_arquivo_tabnet(caminho)
        dfs.append(df)
    return dfs


st.title("📊 Analytics em Saúde Pública — Mortalidade no Brasil (DATASUS/SIM)")
st.caption("Categoria piloto: Mortalidade Geral, 2016–2026")

dfs = carregar_todos_os_arquivos()

# --- Filtros na barra lateral ---
dimensoes_disponiveis = sorted({df["dimensao"].iloc[0] for df in dfs} - {"regiao_x_regiao"})
dimensao_escolhida = st.sidebar.selectbox("Dimensão", dimensoes_disponiveis, index=0)

anos_disponiveis = sorted({df["ano"].iloc[0] for df in dfs})
ano_escolhido = st.sidebar.select_slider("Ano", options=anos_disponiveis, value=anos_disponiveis[-1])

if ano_escolhido >= 2025:
    st.sidebar.warning("⚠️ Dado preliminar/1ª prévia — sujeito a revisão pelo DATASUS.")

# --- Filtra o dataframe correspondente ---
df_filtrado = next(
    df for df in dfs if df["dimensao"].iloc[0] == dimensao_escolhida and df["ano"].iloc[0] == ano_escolhido
)

col_regiao = "Região/Unidade da Federação"
df_exibicao = df_filtrado[~df_filtrado[col_regiao].str.startswith("Região")]  # só estados, sem duplicar total regional
df_exibicao = df_exibicao[df_exibicao[col_regiao] != "Total"]

st.subheader(f"Óbitos por UF — {dimensao_escolhida.replace('_', ' ').title()} ({ano_escolhido})")

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(df_exibicao.drop(columns=["ano", "dimensao"]), use_container_width=True, hide_index=True)

with col2:
    fig = px.bar(
        df_exibicao.sort_values("Total", ascending=False),
        x=col_regiao,
        y="Total",
        title=f"Total de óbitos por UF ({ano_escolhido})",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# --- Série histórica do Total Brasil, por ano ---
st.subheader("Série histórica — Total de óbitos no Brasil")
historico = []
for df in dfs:
    if df["dimensao"].iloc[0] == dimensao_escolhida:
        total_brasil = df[df[col_regiao] == "Total"]["Total"].iloc[0]
        historico.append({"ano": df["ano"].iloc[0], "total": total_brasil})

df_historico = pd.DataFrame(historico).sort_values("ano")
fig_linha = px.line(df_historico, x="ano", y="total", markers=True, title="Evolução anual (Brasil)")
st.plotly_chart(fig_linha, use_container_width=True)