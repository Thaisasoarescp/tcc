import streamlit as st
import pandas as pd
import json
from collections import Counter
from pathlib import Path

# CONFIGURAÇÃO DA PÁGINA

st.set_page_config(
    page_title="Mudanças Climáticas na Mídia",
    page_icon="🌧️",
    layout="wide"
)
 
st.caption("Dashboard de análise das notícias sobre desastres naturais e mudanças climáticas coletadas na mídia brasileira e processadas pelo grupo.")

# CARREGAMENTO DOS DADOS

@st.cache_data
def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)
 
@st.cache_data
def carregar_xlsx(caminho):
    return pd.read_excel(caminho)

tem_json = Path("noticias_processadas_etapas.json").exists()
tem_xlsx = Path("noticias_clima_uol_jp_5anos.xlsx").exists()
 
if not tem_json and not tem_xlsx:
    st.error("Nenhum arquivo de dados encontrado. Coloque os arquivos na mesma pasta que este dashboard.")
    st.stop()

* SEÇÃO 1 - SÉRIE HISTÓRICA XLSX

if tem_xlsx:
    st.header("📅 Série Histórica — 5 Anos (UOL + Jovem Pan)")
 
    df_hist = carregar_xlsx("noticias_clima_uol_jp_5anos.xlsx")

    df_hist["Data"] = pd.to_datetime(df_hist["Data"], dayfirst=True, errors="coerce")
    df_hist = df_hist.dropna(subset=["Data"])
    df_hist["Mes"] = df_hist["Data"].dt.to_period("M").astype(str)

    # Filtro por portal
    portais = df_hist["Portal"].dropna().unique().tolist()
    portal_selecionado = st.multiselect(
        "Filtrar por portal:",
        options=portais,
        default=portais
    )
    df_filtrado = df_hist[df_hist["Portal"].isin(portal_selecionado)]

    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de notícias", len(df_filtrado))
    col2.metric("Portais selecionados", len(portal_selecionado))
    col3.metric("Período", f"{df_filtrado['Data'].min().year} – {df_filtrado['Data'].max().year}")

    # Gráfico: notícias por mês
    por_mes = df_filtrado.groupby("Mes").size().reset_index(name="Quantidade")
    st.subheader("Notícias por mês")
    st.bar_chart(por_mes.set_index("Mes")["Quantidade"])

    # Gráfico: comparativo por portal
    if len(portal_selecionado) > 1:
        st.subheader("Comparativo entre portais")
        por_portal = df_filtrado.groupby(["Mes", "Portal"]).size().reset_index(name="Quantidade")
        por_portal_pivot = por_portal.pivot(index="Mes", columns="Portal", values="Quantidade").fillna(0)
        st.line_chart(por_portal_pivot)
 
    st.divider()

# SEÇÃO 2 — ANÁLISE PLN (JSON)

if tem_json:
    st.header("🔬 Análise de PLN — Jovem Pan")
 
    noticias = carregar_json("noticias_processadas_etapas.json")
 
    # Extrai os tokens de cada notícia para análise de frequência
    todos_tokens = []
    todas_entidades = []
 
    for noticia in noticias:
        pipeline = noticia.get("pipeline_nlp", {})
        tokens = pipeline.get("etapa_5_lista_tokens_ia", [])
        entidades = pipeline.get("etapa_2_entidades", [])
        todos_tokens.extend(tokens)
        todas_entidades.extend([e["texto"] for e in entidades])
 
    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    col1.metric("Notícias processadas", len(noticias))
    col2.metric("Total de tokens", len(todos_tokens))
    col3.metric("Entidades identificadas", len(todas_entidades))
 
    # Gráfico: palavras mais frequentes
    st.subheader("Palavras mais frequentes (após PLN)")
    n_palavras = st.slider("Quantas palavras exibir?", min_value=5, max_value=30, value=15)
    freq = Counter(todos_tokens).most_common(n_palavras)
    df_freq = pd.DataFrame(freq, columns=["Palavra", "Frequência"])
    st.bar_chart(df_freq.set_index("Palavra")["Frequência"])
 
    # Gráfico: entidades mais mencionadas
    st.subheader("Entidades mais mencionadas")
    n_entidades = st.slider("Quantas entidades exibir?", min_value=5, max_value=20, value=10)
    freq_ent = Counter(todas_entidades).most_common(n_entidades)
    df_ent = pd.DataFrame(freq_ent, columns=["Entidade", "Frequência"])
    st.bar_chart(df_ent.set_index("Entidade")["Frequência"])
 
    # Tabela navegável das notícias
    st.subheader("📋 Notícias processadas")
    busca = st.text_input("Buscar por palavra no título:")
    df_noticias = pd.DataFrame([
        {"Título": n.get("titulo", ""), "URL": n.get("url", "")}
        for n in noticias
    ])
    if busca:
        df_noticias = df_noticias[df_noticias["Título"].str.contains(busca, case=False, na=False)]
 
    st.dataframe(df_noticias, use_container_width=True)
 
st.divider()
st.caption("TCC — Análise de Desastres Naturais na Mídia Brasileira | Dados: Jovem Pan & UOL")

