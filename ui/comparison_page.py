"""
Comparison Page — Compare up to 4 stocks/ETFs side by side.

Shows normalized performance chart, comparison table, and signal badges.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.components import render_signal_badge, format_number, PLOTLY_LAYOUT_DEFAULTS

COMPARE_COLORS = ["#2196F3", "#FF9800", "#9C27B0", "#00C805"]

TIMEFRAMES = {
    "1M": ("1mo", "1d", "1 Mes"),
    "3M": ("3mo", "1d", "3 Meses"),
    "6M": ("6mo", "1d", "6 Meses"),
    "1A": ("1y", "1d", "1 Año"),
    "3A": ("3y", "1wk", "3 Años"),
}


def render_comparison_page() -> None:
    """Render the comparison page for up to 4 assets."""
    st.markdown("# ⚖️ Comparar Activos")
    st.caption("Compara hasta 4 acciones o ETFs lado a lado.")

    # ── Ticker management ────────────────────────────────────────────────
    if "compare_tickers" not in st.session_state:
        st.session_state.compare_tickers = []

    col_input, col_add = st.columns([3, 1])
    with col_input:
        new_ticker = st.text_input(
            "Agregar ticker",
            placeholder="Ej: AAPL, AMX.MX, VOO",
            key="compare_new_ticker",
            label_visibility="collapsed",
        )
    with col_add:
        can_add = len(st.session_state.compare_tickers) < 4
        if st.button("➕ Agregar", disabled=not can_add, use_container_width=True):
            t = new_ticker.strip().upper()
            if t and t not in st.session_state.compare_tickers:
                st.session_state.compare_tickers.append(t)
                st.rerun()
            elif t in st.session_state.compare_tickers:
                st.warning(f"{t} ya está en la lista.")

    # Show current tickers with remove buttons
    if st.session_state.compare_tickers:
        cols = st.columns(len(st.session_state.compare_tickers))
        for i, ticker in enumerate(st.session_state.compare_tickers):
            with cols[i]:
                st.markdown(
                    f"<div style='background:{COMPARE_COLORS[i]}22; border:1px solid {COMPARE_COLORS[i]};"
                    f" border-radius:8px; padding:6px 12px; text-align:center; font-weight:600;'>"
                    f"{ticker}</div>",
                    unsafe_allow_html=True,
                )
                if st.button("✕ Quitar", key=f"rm_{ticker}", use_container_width=True):
                    st.session_state.compare_tickers.remove(ticker)
                    st.rerun()
    else:
        st.info("Agrega al menos 2 tickers para comparar.")
        return

    if len(st.session_state.compare_tickers) < 2:
        st.info("Agrega al menos 2 tickers para comparar.")
        return

    tickers = st.session_state.compare_tickers

    # ── Timeframe selector ───────────────────────────────────────────────
    st.markdown("---")
    tf_keys = list(TIMEFRAMES.keys())
    selected_tf = st.radio(
        "Período", tf_keys, horizontal=True, index=3, key="compare_tf",
        label_visibility="collapsed",
    )
    period, interval, tf_label = TIMEFRAMES[selected_tf]

    # ── Load data ────────────────────────────────────────────────────────
    with st.spinner("Cargando datos..."):
        infos = {}
        ohlcvs = {}
        signals = {}

        for t in tickers:
            infos[t] = _load_info(t)
            ohlcvs[t] = _load_ohlcv(t, period, interval)
            signals[t] = _load_signal(t)

    # ── Normalized performance chart ─────────────────────────────────────
    st.markdown(f"### 📈 Rendimiento Comparado — {tf_label}")
    fig = _build_performance_chart(tickers, ohlcvs)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudieron generar las gráficas de rendimiento.")

    # ── Comparison table ─────────────────────────────────────────────────
    st.markdown("### 📊 Tabla Comparativa")
    _render_comparison_table(tickers, infos, signals)

    # ── Signal badges ────────────────────────────────────────────────────
    st.markdown("### 🚦 Señales")
    sig_cols = st.columns(len(tickers))
    for i, t in enumerate(tickers):
        with sig_cols[i]:
            st.markdown(f"**{t}**")
            sig = signals.get(t)
            if sig:
                render_signal_badge(sig.signal, sig.confidence, sig.score)
            else:
                st.caption("Señal no disponible")

    # ── Performance summary ──────────────────────────────────────────────
    st.markdown("### 🏆 Resumen de Rendimiento")
    _render_performance_summary(tickers, ohlcvs)


# ── Data loading (cached) ───────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _load_info(ticker: str):
    try:
        from data.fetcher import get_stock_info
        return get_stock_info(ticker)
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _load_ohlcv(ticker: str, period: str, interval: str):
    try:
        from data.fetcher import get_ohlcv
        return get_ohlcv(ticker, period=period, interval=interval)
    except Exception:
        return None


def _load_signal(ticker: str):
    try:
        from analysis.signals import generate_signal
        from data.fetcher import get_ohlcv
        ohlcv = get_ohlcv(ticker, period="6mo", interval="1d")
        if ohlcv is None:
            return None
        return generate_signal(ohlcv)
    except Exception:
        return None


# ── Chart builders ───────────────────────────────────────────────────────────

def _build_performance_chart(tickers, ohlcvs) -> go.Figure:
    """Normalized performance chart (base 100)."""
    fig = go.Figure()
    has_data = False

    for i, t in enumerate(tickers):
        ohlcv = ohlcvs.get(t)
        if ohlcv is None or ohlcv.df.empty:
            continue
        df = ohlcv.df
        if "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if close.empty:
            continue
        normalized = (close / close.iloc[0]) * 100
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized,
            mode="lines",
            name=t,
            line=dict(color=COMPARE_COLORS[i % len(COMPARE_COLORS)], width=2),
        ))
        has_data = True

    if not has_data:
        return None

    fig.add_hline(y=100, line_dash="dot", line_color="#666", line_width=0.8,
                  annotation_text="Base (100)", annotation_position="right")

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=420,
        yaxis_title="Rendimiento Normalizado (Base 100)",
        hovermode="x unified",
    )
    return fig


# ── Table renderers ──────────────────────────────────────────────────────────

def _render_comparison_table(tickers, infos, signals) -> None:
    """Side-by-side comparison table."""
    rows = []
    metrics = [
        ("Precio", lambda i, s: format_number(i.price, prefix="$", abbreviate=False) if i else "N/D"),
        ("Cambio %", lambda i, s: f"{i.change_pct:+.2f}%" if i else "N/D"),
        ("Cap. Mercado", lambda i, s: format_number(i.market_cap, prefix="$") if i else "N/D"),
        ("P/E", lambda i, s: format_number(i.pe_ratio, abbreviate=False) if i else "N/D"),
        ("Dividendo", lambda i, s: format_number(i.dividend_yield, suffix="%", abbreviate=False) if i else "N/D"),
        ("Beta", lambda i, s: format_number(i.beta, abbreviate=False) if i else "N/D"),
        ("RSI", lambda i, s: f"{s.rsi_value:.1f}" if s else "N/D"),
        ("Señal", lambda i, s: s.signal if s else "N/D"),
    ]

    for label, fn in metrics:
        row = {"Métrica": label}
        for t in tickers:
            info = infos.get(t)
            sig = signals.get(t)
            try:
                row[t] = fn(info, sig)
            except Exception:
                row[t] = "N/D"
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.set_index("Métrica")
    st.dataframe(df, use_container_width=True)


def _render_performance_summary(tickers, ohlcvs) -> None:
    """Best/worst performer and average return."""
    returns = {}
    for t in tickers:
        ohlcv = ohlcvs.get(t)
        if ohlcv is None or ohlcv.df.empty:
            continue
        close = ohlcv.df["Close"].dropna()
        if len(close) < 2:
            continue
        pct = ((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100
        returns[t] = pct

    if not returns:
        st.info("No hay datos suficientes para el resumen.")
        return

    best = max(returns, key=returns.get)
    worst = min(returns, key=returns.get)
    avg = sum(returns.values()) / len(returns)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🥇 Mejor Rendimiento", best, f"{returns[best]:+.2f}%")
    with col2:
        st.metric("🥉 Peor Rendimiento", worst, f"{returns[worst]:+.2f}%")
    with col3:
        st.metric("📊 Promedio", f"{avg:+.2f}%")
