import streamlit as st

st.set_page_config(
    page_title="StockWatch — Análisis de Inversión",
    page_icon="📈",
    layout="wide"
)

# Navigation state
if "page" not in st.session_state:
    st.session_state.page = "search"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "compare_tickers" not in st.session_state:
    st.session_state.compare_tickers = []

# Sidebar navigation
with st.sidebar:
    st.title("📈 StockWatch")
    st.caption("Análisis de Inversión — MX + USA")
    st.divider()
    if st.button("🔍 Búsqueda", use_container_width=True):
        st.session_state.page = "search"
    if st.button("📊 Análisis", use_container_width=True, disabled=st.session_state.selected_ticker is None):
        st.session_state.page = "detail"
    if st.button("⚖️ Comparar", use_container_width=True):
        st.session_state.page = "comparison"
    st.divider()
    st.caption("Datos: Yahoo Finance (yfinance)")
    st.caption("Broker referencia: GBM")

# Route to page
from ui.search_page import render_search_page
from ui.detail_page import render_detail_page
from ui.comparison_page import render_comparison_page

if st.session_state.page == "search":
    render_search_page()
elif st.session_state.page == "detail":
    render_detail_page()
elif st.session_state.page == "comparison":
    render_comparison_page()
