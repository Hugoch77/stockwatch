"""
Detail Page — Full investment analysis for a single stock/ETF.

Sections: price header, signal badge, metrics, candlestick chart,
RSI/MACD indicators, signal breakdown, fundamental data, historical table.
"""
import streamlit as st
import pandas as pd
from ui.components import (
    render_price_header,
    render_metric_row,
    render_signal_badge,
    render_candlestick_chart,
    render_rsi_chart,
    render_macd_chart,
    render_signal_reasons,
    render_period_summary,
    render_investment_simulator,
    format_number,
)

TIMEFRAMES = {
    "1S": ("7d", "1h", "1 Semana"),
    "1M": ("1mo", "1d", "1 Mes"),
    "3M": ("3mo", "1d", "3 Meses"),
    "6M": ("6mo", "1d", "6 Meses"),
    "1A": ("1y", "1d", "1 Año"),
    "3A": ("3y", "1wk", "3 Años"),
    "5A": ("5y", "1wk", "5 Años"),
    "MAX": ("max", "1mo", "Máximo"),
}


def render_detail_page() -> None:
    """Render the full analysis page for a single ticker."""
    ticker = st.session_state.get("selected_ticker")
    if not ticker:
        st.warning("No se ha seleccionado ningún activo. Usa el buscador.")
        if st.button("← Ir a búsqueda"):
            st.session_state.page = "search"
            st.rerun()
        return

    # ── Back button ──────────────────────────────────────────────────────
    col_back, col_breadcrumb = st.columns([1, 5])
    with col_back:
        if st.button("← Volver"):
            st.session_state.page = "search"
            st.rerun()
    with col_breadcrumb:
        st.caption(f"Búsqueda › **{ticker}**")

    # ── Load stock info ──────────────────────────────────────────────────
    info = _load_stock_info(ticker)
    if info is None:
        st.error(f"No se pudo obtener información para **{ticker}**. Verifica el ticker.")
        return

    # ── Price header + Signal ────────────────────────────────────────────
    col_header, col_signal = st.columns([3, 1])
    with col_header:
        render_price_header(info)
    with col_signal:
        signal_result = _load_signal(ticker)
        if signal_result:
            render_signal_badge(signal_result.signal, signal_result.confidence, signal_result.score)

    # ── Key metrics ──────────────────────────────────────────────────────
    st.markdown("---")
    render_metric_row(info)

    # ── Timeframe selector ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Gráfica de Precios")

    tf_keys = list(TIMEFRAMES.keys())
    selected_tf = st.radio(
        "Período",
        tf_keys,
        horizontal=True,
        index=4,  # default to 1A
        key="detail_timeframe",
        label_visibility="collapsed",
    )
    period, interval, tf_label = TIMEFRAMES[selected_tf]

    # ── Load OHLCV + indicators ──────────────────────────────────────────
    ohlcv = _load_ohlcv(ticker, period, interval)
    if ohlcv is None:
        st.error("No se pudieron cargar los datos históricos.")
        return

    indicators = _load_indicators(ticker, ohlcv)

    # ── Period performance summary ────────────────────────────────────────
    render_period_summary(ohlcv, tf_label)

    # ── Candlestick chart ────────────────────────────────────────────────
    fig_candle = render_candlestick_chart(
        ohlcv, indicators=indicators, title=f"{ticker} — {tf_label}"
    )
    st.plotly_chart(fig_candle, use_container_width=True)

    # ── Technical indicators ─────────────────────────────────────────────
    if indicators:
        st.markdown("### 📉 Indicadores Técnicos")
        tab_rsi, tab_macd = st.tabs(["RSI", "MACD"])

        with tab_rsi:
            fig_rsi = render_rsi_chart(indicators)
            st.plotly_chart(fig_rsi, use_container_width=True)

        with tab_macd:
            fig_macd = render_macd_chart(indicators)
            st.plotly_chart(fig_macd, use_container_width=True)

        # Indicator values table
        with st.expander("📊 Valores actuales de indicadores"):
            _render_indicator_values(indicators)

    # ── Signal breakdown ─────────────────────────────────────────────────
    if signal_result:
        st.markdown("---")
        render_signal_reasons(signal_result)

    # ── Fundamental data ─────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📋 Datos Fundamentales", expanded=False):
        _render_fundamentals(info)

    # ── Historical data table ────────────────────────────────────────────
    with st.expander("📜 Datos Históricos (últimos 30 registros)", expanded=False):
        _render_history_table(ohlcv)

    # ── Investment simulator ─────────────────────────────────────────────
    st.markdown("---")
    with st.expander("💰 Simulador de Inversión", expanded=False):
        # Load max-history OHLCV for simulator so projections use all available data
        ohlcv_max = _load_ohlcv(ticker, "max", "1mo")
        render_investment_simulator(ohlcv_max if ohlcv_max else ohlcv, info)


# ── Data loading helpers (cached) ────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _load_stock_info(ticker: str):
    """Load stock info with caching."""
    try:
        from data.fetcher import get_stock_info
        return get_stock_info(ticker)
    except Exception as e:
        st.error(f"Error cargando info: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _load_ohlcv(ticker: str, period: str, interval: str):
    """Load OHLCV data with caching."""
    try:
        from data.fetcher import get_ohlcv
        return get_ohlcv(ticker, period=period, interval=interval)
    except Exception as e:
        st.error(f"Error cargando datos históricos: {e}")
        return None


def _load_indicators(ticker: str, ohlcv):
    """Compute technical indicators."""
    try:
        from analysis.indicators import compute_indicators
        return compute_indicators(ohlcv)
    except ImportError:
        return None
    except Exception:
        return None


def _load_signal(ticker: str):
    """Generate signal for the ticker."""
    try:
        from analysis.signals import generate_signal
        from data.fetcher import get_ohlcv
        ohlcv = get_ohlcv(ticker, period="6mo", interval="1d")
        if ohlcv is None:
            return None
        return generate_signal(ohlcv)
    except ImportError:
        return None
    except Exception:
        return None


# ── Sub-renderers ────────────────────────────────────────────────────────────

def _render_indicator_values(indicators) -> None:
    """Table of current indicator values."""
    data = {}
    if indicators.rsi is not None and not indicators.rsi.empty:
        data["RSI (14)"] = f"{indicators.rsi.iloc[-1]:.2f}"
    if indicators.macd is not None and not indicators.macd.empty:
        data["MACD"] = f"{indicators.macd.iloc[-1]:.4f}"
    if indicators.macd_signal_line is not None and not indicators.macd_signal_line.empty:
        data["Señal MACD"] = f"{indicators.macd_signal_line.iloc[-1]:.4f}"
    if indicators.macd_hist is not None and not indicators.macd_hist.empty:
        data["Histograma MACD"] = f"{indicators.macd_hist.iloc[-1]:.4f}"
    if indicators.bb_upper is not None and not indicators.bb_upper.empty:
        data["BB Superior"] = f"{indicators.bb_upper.iloc[-1]:.2f}"
    if indicators.bb_lower is not None and not indicators.bb_lower.empty:
        data["BB Inferior"] = f"{indicators.bb_lower.iloc[-1]:.2f}"
    if indicators.ema_short is not None and not indicators.ema_short.empty:
        data["EMA 20"] = f"{indicators.ema_short.iloc[-1]:.2f}"
    if indicators.ema_long is not None and not indicators.ema_long.empty:
        data["EMA 50"] = f"{indicators.ema_long.iloc[-1]:.2f}"
    if indicators.sma_200 is not None and not indicators.sma_200.empty:
        data["SMA 200"] = f"{indicators.sma_200.iloc[-1]:.2f}"

    if data:
        col1, col2, col3 = st.columns(3)
        items = list(data.items())
        for i, (label, val) in enumerate(items):
            with [col1, col2, col3][i % 3]:
                st.metric(label, val)
    else:
        st.info("Indicadores no disponibles.")


def _render_fundamentals(info) -> None:
    """Render fundamental data section."""
    cols = st.columns(3)

    with cols[0]:
        st.markdown("**Valoración**")
        st.write(f"- P/E: {format_number(info.pe_ratio, abbreviate=False)}")
        st.write(f"- EPS: {format_number(info.eps, prefix='$', abbreviate=False)}")
        st.write(f"- Cap. Mercado: {format_number(info.market_cap, prefix='$')}")
    with cols[1]:
        st.markdown("**Dividendos y Riesgo**")
        st.write(f"- Rendimiento: {format_number(info.dividend_yield, suffix='%', abbreviate=False)}")
        st.write(f"- Tasa dividendo: {format_number(info.dividend_rate, prefix='$', abbreviate=False)}")
        st.write(f"- Beta: {format_number(info.beta, abbreviate=False)}")
    with cols[2]:
        st.markdown("**Clasificación**")
        st.write(f"- Sector: {info.sector or 'N/D'}")
        st.write(f"- Industria: {info.industry or 'N/D'}")
        # ETF fields
        if hasattr(info, "expense_ratio") and info.expense_ratio:
            st.write(f"- Ratio de gastos: {format_number(info.expense_ratio, suffix='%', abbreviate=False)}")
        if hasattr(info, "category") and info.category:
            st.write(f"- Categoría: {info.category}")

    # Description
    if info.description:
        st.markdown("**Descripción**")
        desc = info.description
        if len(desc) > 500:
            if st.session_state.get(f"show_full_desc_{info.ticker}", False):
                st.write(desc)
                if st.button("Ver menos", key=f"less_{info.ticker}"):
                    st.session_state[f"show_full_desc_{info.ticker}"] = False
                    st.rerun()
            else:
                st.write(desc[:500] + "...")
                if st.button("Ver más", key=f"more_{info.ticker}"):
                    st.session_state[f"show_full_desc_{info.ticker}"] = True
                    st.rerun()
        else:
            st.write(desc)


def _render_history_table(ohlcv) -> None:
    """Show last 30 OHLCV rows."""
    df = ohlcv.df.copy()
    df = df.sort_index(ascending=False).head(30)
    display_cols = ["Open", "High", "Low", "Close", "Volume"]
    available = [c for c in display_cols if c in df.columns]
    if available:
        display_df = df[available].copy()
        display_df.columns = ["Apertura", "Máximo", "Mínimo", "Cierre", "Volumen"][:len(available)]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No hay datos históricos disponibles.")
