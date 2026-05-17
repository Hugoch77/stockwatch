"""Reusable UI components for StockWatch."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional
from datetime import datetime

# Analysis imports are done lazily inside render_investment_simulator to
# avoid circular dependencies and missing-module crashes at import time.

# ── Color constants ──────────────────────────────────────────────────────────
COLOR_BULLISH = "#00C805"
COLOR_BEARISH = "#FF3131"
COLOR_NEUTRAL = "#888888"
COLOR_PRICE = "#2196F3"
COLOR_EMA_SHORT = "#FF9800"
COLOR_EMA_LONG = "#9C27B0"

PLOTLY_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(14,17,23,1)",
    font=dict(color="#FAFAFA"),
    margin=dict(l=50, r=20, t=40, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


# ── Format helpers ───────────────────────────────────────────────────────────

def format_number(
    value: Optional[float],
    prefix: str = "",
    suffix: str = "",
    decimals: int = 2,
    abbreviate: bool = True,
) -> str:
    """Format a number for display. None → 'N/D'. Supports abbreviation."""
    if value is None:
        return "N/D"
    if abbreviate and abs(value) >= 1_000_000_000_000:
        formatted = f"{value / 1_000_000_000_000:,.{decimals}f}T"
    elif abbreviate and abs(value) >= 1_000_000_000:
        formatted = f"{value / 1_000_000_000:,.{decimals}f}B"
    elif abbreviate and abs(value) >= 1_000_000:
        formatted = f"{value / 1_000_000:,.{decimals}f}M"
    else:
        formatted = f"{value:,.{decimals}f}"
    return f"{prefix}{formatted}{suffix}"


def _color_for_signal(signal: str) -> str:
    """Return hex color for a signal string."""
    s = signal.upper()
    if s == "COMPRA":
        return COLOR_BULLISH
    if s == "VENTA":
        return COLOR_BEARISH
    return COLOR_NEUTRAL


def _icon_for_signal(signal: str) -> str:
    s = signal.upper()
    if s == "COMPRA":
        return "▲"
    if s == "VENTA":
        return "▼"
    return "◆"


# ── Signal badge ─────────────────────────────────────────────────────────────

def render_signal_badge(signal: str, confidence: str, score: int) -> None:
    """Render a large, prominent signal badge with color coding."""
    color = _color_for_signal(signal)
    icon = _icon_for_signal(signal)
    st.markdown(
        f"""
        <div style="
            background-color: {color}20;
            border: 2px solid {color};
            border-radius: 12px;
            padding: 16px 24px;
            text-align: center;
            margin-bottom: 12px;
        ">
            <div style="font-size: 2.4rem; font-weight: 800; color: {color};">
                {icon} {signal}
            </div>
            <div style="font-size: 1rem; color: {color}; margin-top: 4px;">
                Confianza: <b>{confidence}</b> &nbsp;|&nbsp; Puntuación: <b>{score}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Price header ─────────────────────────────────────────────────────────────

def render_price_header(info) -> None:
    """Show asset name, market flag, price, change, and metadata."""
    flag = "🇲🇽" if info.market == "MX" else "🇺🇸"
    asset_badge_color = "#1976D2" if info.asset_type == "ETF" else "#7B1FA2"
    change_color = COLOR_BULLISH if info.change >= 0 else COLOR_BEARISH
    change_sign = "+" if info.change >= 0 else ""
    currency_sym = "$" if info.currency in ("USD", "MXN") else ""
    currency_label = info.currency

    col_name, col_price = st.columns([3, 2])
    with col_name:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                <span style="font-size:1.6rem; font-weight:700;">{info.name}</span>
                <span style="font-size:1.3rem;">{flag}</span>
                <span style="background:{asset_badge_color}; color:#fff; padding:2px 10px;
                      border-radius:6px; font-size:0.8rem; font-weight:600;">
                    {info.asset_type}
                </span>
                <span style="color:#999; font-size:0.9rem;">{info.ticker}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_price:
        st.markdown(
            f"""
            <div style="text-align:right;">
                <div style="font-size:2rem; font-weight:800;">
                    {currency_sym}{info.price:,.2f} <span style="font-size:0.9rem; color:#aaa;">{currency_label}</span>
                </div>
                <div style="font-size:1.1rem; color:{change_color}; font-weight:600;">
                    {change_sign}{info.change:,.2f} ({change_sign}{info.change_pct:.2f}%)
                </div>
                <div style="font-size:0.75rem; color:#666; margin-top:2px;">
                    Actualizado: {datetime.now().strftime("%d/%m/%Y %H:%M")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Metric row ───────────────────────────────────────────────────────────────

def render_metric_row(info) -> None:
    """Render key metrics in a horizontal row."""
    cols = st.columns(4)

    with cols[0]:
        st.metric("Volumen", format_number(info.volume, abbreviate=True))
        st.caption(f"Prom: {format_number(info.avg_volume, abbreviate=True)}")
    with cols[1]:
        st.metric("Cap. de Mercado", format_number(info.market_cap, prefix="$"))
    with cols[2]:
        st.metric("P/E", format_number(info.pe_ratio, abbreviate=False))
    with cols[3]:
        st.metric("Rend. Dividendo", format_number(info.dividend_yield, suffix="%", abbreviate=False))

    cols2 = st.columns(4)
    with cols2[0]:
        st.metric("Beta", format_number(info.beta, abbreviate=False))
    with cols2[1]:
        st.metric("EPS", format_number(info.eps, prefix="$", abbreviate=False))
    with cols2[2]:
        st.metric("Máx 52 sem", format_number(info.week_52_high, prefix="$", abbreviate=False))
    with cols2[3]:
        st.metric("Mín 52 sem", format_number(info.week_52_low, prefix="$", abbreviate=False))

    # 52-week range progress bar
    if info.week_52_high and info.week_52_low and info.week_52_high > info.week_52_low:
        position = (info.price - info.week_52_low) / (info.week_52_high - info.week_52_low)
        position = max(0.0, min(1.0, position))
        bar_color = COLOR_BULLISH if position > 0.5 else COLOR_BEARISH
        st.markdown(
            f"""
            <div style="margin:4px 0 12px 0;">
                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#888;">
                    <span>Mín ${info.week_52_low:,.2f}</span>
                    <span>Rango 52 semanas</span>
                    <span>Máx ${info.week_52_high:,.2f}</span>
                </div>
                <div style="background:#333; border-radius:4px; height:8px; margin-top:2px; position:relative;">
                    <div style="background:{bar_color}; width:{position*100:.1f}%; height:100%;
                                border-radius:4px;"></div>
                    <div style="position:absolute; top:-3px; left:{position*100:.1f}%;
                                width:3px; height:14px; background:#fff; border-radius:2px;
                                transform:translateX(-50%);"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Period summary ───────────────────────────────────────────────────────────

def render_period_summary(ohlcv, tf_label: str) -> None:
    """
    Render a 3-column summary row showing period start price, current price,
    and percentage change for the selected timeframe.
    """
    df = ohlcv.df.copy()

    if df is None or len(df) < 2:
        st.info("Sin datos suficientes para este período.")
        return

    currency = getattr(ohlcv, "currency", "USD")
    if currency in ("USD", "MXN"):
        sym = "$"
    else:
        sym = f"{currency} "

    precio_inicio = df["Open"].iloc[0]
    precio_actual = df["Close"].iloc[-1]
    variacion_pct = ((precio_actual - precio_inicio) / precio_inicio) * 100

    is_positive = variacion_pct >= 0
    arrow = "▲" if is_positive else "▼"
    color = COLOR_BULLISH if is_positive else COLOR_BEARISH
    sign = "+" if is_positive else ""

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 12px 20px;
            margin: 8px 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        ">
            <span style="font-size:0.8rem; color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">
                Rendimiento del período: {tf_label}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Inicio del período",
            value=f"{sym}{precio_inicio:,.2f}",
        )

    with col2:
        st.metric(
            label="Precio actual",
            value=f"{sym}{precio_actual:,.2f}",
        )

    with col3:
        # Use st.markdown for custom green/red coloring on the variation
        st.markdown(
            f"""
            <div>
                <div style="font-size:0.875rem; color:#aaa; margin-bottom:4px;">Variación del período</div>
                <div style="font-size:1.6rem; font-weight:700; color:{color}; line-height:1.2;">
                    {arrow} {sign}{variacion_pct:.2f}%
                </div>
                <div style="font-size:0.75rem; color:#666; margin-top:2px;">
                    {sign}{sym}{abs(precio_actual - precio_inicio):,.2f} desde inicio
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Candlestick chart ────────────────────────────────────────────────────────

def render_candlestick_chart(ohlcv, indicators=None, title: str = "") -> go.Figure:
    """Full candlestick chart with volume subplot and optional overlays."""
    df = ohlcv.df.copy()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=[title or f"{ohlcv.ticker} — Precio", "Volumen"],
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            increasing_line_color=COLOR_BULLISH,
            decreasing_line_color=COLOR_BEARISH,
            increasing_fillcolor=COLOR_BULLISH,
            decreasing_fillcolor=COLOR_BEARISH,
            name="Precio",
        ),
        row=1, col=1,
    )

    # Volume bars
    colors = [
        COLOR_BULLISH if c >= o else COLOR_BEARISH
        for o, c in zip(df["Open"], df["Close"])
    ]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], marker_color=colors, opacity=0.5, name="Volumen", showlegend=False),
        row=2, col=1,
    )

    # Indicator overlays
    if indicators is not None:
        # EMA short (20)
        if indicators.ema_short is not None and not indicators.ema_short.empty:
            fig.add_trace(
                go.Scatter(x=indicators.ema_short.index, y=indicators.ema_short, mode="lines",
                           line=dict(color=COLOR_EMA_SHORT, width=1.2), name="EMA 20"),
                row=1, col=1,
            )
        # EMA long (50)
        if indicators.ema_long is not None and not indicators.ema_long.empty:
            fig.add_trace(
                go.Scatter(x=indicators.ema_long.index, y=indicators.ema_long, mode="lines",
                           line=dict(color=COLOR_EMA_LONG, width=1.2), name="EMA 50"),
                row=1, col=1,
            )
        # SMA 200
        if indicators.sma_200 is not None and not indicators.sma_200.empty:
            fig.add_trace(
                go.Scatter(x=indicators.sma_200.index, y=indicators.sma_200, mode="lines",
                           line=dict(color="#FFEB3B", width=1, dash="dot"), name="SMA 200"),
                row=1, col=1,
            )
        # Bollinger Bands
        if indicators.bb_upper is not None and not indicators.bb_upper.empty:
            fig.add_trace(
                go.Scatter(x=indicators.bb_upper.index, y=indicators.bb_upper, mode="lines",
                           line=dict(color="rgba(33,150,243,0.4)", width=0.8), name="BB Superior",
                           showlegend=False),
                row=1, col=1,
            )
            fig.add_trace(
                go.Scatter(x=indicators.bb_lower.index, y=indicators.bb_lower, mode="lines",
                           line=dict(color="rgba(33,150,243,0.4)", width=0.8),
                           fill="tonexty", fillcolor="rgba(33,150,243,0.07)",
                           name="Bollinger Bands"),
                row=1, col=1,
            )

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=560,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=True,
        xaxis2_rangeslider_thickness=0.04,
        yaxis_title=f"Precio ({ohlcv.currency})",
        yaxis2_title="Volumen",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")

    return fig


# ── RSI chart ────────────────────────────────────────────────────────────────

def render_rsi_chart(indicators) -> go.Figure:
    """RSI chart with overbought/oversold zones."""
    fig = go.Figure()

    rsi = indicators.rsi.dropna()

    # Overbought zone fill (above 70)
    fig.add_trace(go.Scatter(
        x=rsi.index, y=[70] * len(rsi), mode="lines",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=rsi.index, y=[100] * len(rsi), mode="lines",
        line=dict(color="rgba(0,0,0,0)"),
        fill="tonexty", fillcolor="rgba(255,49,49,0.1)",
        showlegend=False,
    ))

    # Oversold zone fill (below 30)
    fig.add_trace(go.Scatter(
        x=rsi.index, y=[0] * len(rsi), mode="lines",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=rsi.index, y=[30] * len(rsi), mode="lines",
        line=dict(color="rgba(0,0,0,0)"),
        fill="tonexty", fillcolor="rgba(0,200,5,0.1)",
        showlegend=False,
    ))

    # RSI line
    fig.add_trace(go.Scatter(
        x=rsi.index, y=rsi, mode="lines",
        line=dict(color=COLOR_PRICE, width=1.8), name="RSI",
    ))

    # Reference lines
    fig.add_hline(y=70, line_dash="dash", line_color=COLOR_BEARISH, line_width=1,
                  annotation_text="Sobrecompra (70)", annotation_position="top right")
    fig.add_hline(y=30, line_dash="dash", line_color=COLOR_BULLISH, line_width=1,
                  annotation_text="Sobreventa (30)", annotation_position="bottom right")
    fig.add_hline(y=50, line_dash="dot", line_color="#555", line_width=0.8)

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title="RSI (14)",
        height=250,
        yaxis=dict(range=[0, 100], title="RSI"),
        showlegend=False,
    )
    return fig


# ── MACD chart ───────────────────────────────────────────────────────────────

def render_macd_chart(indicators) -> go.Figure:
    """MACD chart with histogram."""
    fig = go.Figure()

    macd = indicators.macd.dropna()
    signal_line = indicators.macd_signal_line.dropna()
    hist = indicators.macd_hist.dropna()

    # Histogram
    hist_colors = [COLOR_BULLISH if v >= 0 else COLOR_BEARISH for v in hist]
    fig.add_trace(go.Bar(
        x=hist.index, y=hist, marker_color=hist_colors,
        opacity=0.6, name="Histograma",
    ))

    # MACD line
    fig.add_trace(go.Scatter(
        x=macd.index, y=macd, mode="lines",
        line=dict(color=COLOR_PRICE, width=1.5), name="MACD",
    ))

    # Signal line
    fig.add_trace(go.Scatter(
        x=signal_line.index, y=signal_line, mode="lines",
        line=dict(color=COLOR_EMA_SHORT, width=1.5), name="Señal",
    ))

    # Zero line
    fig.add_hline(y=0, line_color="#555", line_width=0.8)

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title="MACD (12, 26, 9)",
        height=250,
        yaxis_title="MACD",
    )
    return fig


# ── Signal reasons ───────────────────────────────────────────────────────────

def render_signal_reasons(signal_result) -> None:
    """Show a breakdown of signal components."""
    st.markdown("#### 📊 Desglose de la Señal")

    if not signal_result.reasons:
        st.info("No hay detalles de componentes disponibles.")
        return

    for reason in signal_result.reasons:
        if isinstance(reason, dict):
            name = reason.get("name", reason.get("component", ""))
            score_val = reason.get("score", 0)
            explanation = reason.get("explanation", reason.get("reason", ""))
        elif isinstance(reason, str):
            st.markdown(f"- {reason}")
            continue
        else:
            name = getattr(reason, "name", getattr(reason, "component", ""))
            score_val = getattr(reason, "score", 0)
            explanation = getattr(reason, "explanation", getattr(reason, "reason", ""))

        if score_val > 0:
            emoji, color = "🟢", COLOR_BULLISH
        elif score_val < 0:
            emoji, color = "🔴", COLOR_BEARISH
        else:
            emoji, color = "⚪", COLOR_NEUTRAL

        st.markdown(
            f"{emoji} **{name}** "
            f"<span style='color:{color}; font-weight:600;'>({'+' if score_val > 0 else ''}{score_val})</span>"
            f" — {explanation}",
            unsafe_allow_html=True,
        )

    # Summary row for indicator values
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        rsi_color = COLOR_BEARISH if signal_result.rsi_value > 70 else (
            COLOR_BULLISH if signal_result.rsi_value < 30 else COLOR_NEUTRAL)
        st.markdown(f"**RSI:** <span style='color:{rsi_color}'>{signal_result.rsi_value:.1f}</span> — {signal_result.rsi_signal}",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"**MACD:** {signal_result.macd_signal}")
    with c3:
        st.markdown(f"**Bollinger:** {signal_result.bb_signal}")
    with c4:
        st.markdown(f"**Tendencia:** {signal_result.trend_signal}")


# ── Investment Simulator ──────────────────────────────────────────────────────

def _currency_symbol(currency: str) -> str:
    """Map a currency code to a display symbol."""
    if currency == "USD":
        return "$"
    if currency in ("MXN", "MX$"):
        return "MX$"
    return f"{currency} "


def _fmt_currency(value: float, sym: str) -> str:
    """Format a monetary value with thousands separator."""
    return f"{sym}{value:,.2f}"


def _fmt_pct(value: float) -> str:
    """Format a percentage with arrow indicator."""
    arrow = "▲" if value >= 0 else "▼"
    sign = "+" if value >= 0 else ""
    return f"{arrow} {sign}{value:.2f}%"


def render_investment_simulator(ohlcv_data, stock_info) -> None:
    """
    Render a full investment simulator UI component.

    Parameters
    ----------
    ohlcv_data  : OHLCVData or None — historical price data
    stock_info  : StockInfo         — asset metadata (currency, name, etc.)
    """
    st.markdown("## 💰 Simulador de Inversión")

    # ── Edge-case guard ───────────────────────────────────────────────────
    if ohlcv_data is None or ohlcv_data.df is None or len(ohlcv_data.df) < 30:
        st.info(
            "Se necesitan al menos 30 días de datos históricos para calcular la simulación."
        )
        return

    # ── Lazy imports ───────────────────────────────────────────────────────
    try:
        from analysis.simulator import (
            calculate_historical_returns,
            simulate_investment,
            get_simulation_disclaimer,
        )
    except ImportError as exc:
        st.error(f"Módulo de simulación no disponible: {exc}")
        return

    df = ohlcv_data.df.copy()
    currency = getattr(stock_info, "currency", "USD") if stock_info else "USD"
    sym = _currency_symbol(currency)

    # ── Compute historical metrics ─────────────────────────────────────────
    hist = calculate_historical_returns(df)
    data_years = hist.get("data_years", 0.0)

    if data_years < 1.0:
        st.info(
            "Se necesitan al menos 12 meses de datos históricos para calcular la simulación."
        )
        return

    # ── Investment amount input ────────────────────────────────────────────
    amount = st.number_input(
        f"Monto a invertir ({sym})",
        min_value=100.0,
        value=10_000.0,
        step=1_000.0,
        format="%.2f",
        key="sim_amount",
    )

    # ── Historical metrics row ─────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        cagr_pct = hist["cagr"] * 100
        cagr_color = COLOR_BULLISH if cagr_pct >= 0 else COLOR_BEARISH
        st.markdown(
            f"**Rendimiento Anual Histórico**<br>"
            f"<span style='font-size:1.4rem; font-weight:700; color:{cagr_color};'>"
            f"{_fmt_pct(cagr_pct)}</span>",
            unsafe_allow_html=True,
        )
    with m2:
        vol_pct = hist["volatility"] * 100
        st.markdown(
            f"**Volatilidad Anualizada**<br>"
            f"<span style='font-size:1.4rem; font-weight:700; color:{COLOR_NEUTRAL};'>"
            f"{vol_pct:.1f}%</span>",
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"**Datos disponibles**<br>"
            f"<span style='font-size:1.4rem; font-weight:700;'>"
            f"{data_years:.1f} años</span>",
            unsafe_allow_html=True,
        )

    # ── Low-data notice ────────────────────────────────────────────────────
    if data_years < 3.0:
        st.warning(
            f"⚠️ Solo hay {data_years:.1f} años de datos. "
            "Los escenarios optimista y pesimista son menos confiables con datos limitados."
        )

    # ── Run simulation ─────────────────────────────────────────────────────
    sim_rows = simulate_investment(float(amount), hist)
    if not sim_rows:
        st.info("No se pudieron calcular proyecciones con los datos disponibles.")
        return

    # ── Compounding explanation header ────────────────────────────────────
    st.info(
        "💡 **Proyecciones con rendimiento compuesto** — fórmula: Capital × (1 + CAGR)^años\n\n"
        "Las acciones y ETFs generan rendimiento compuesto: cada año, las ganancias se "
        "reinvierten y generan más ganancias sobre sí mismas."
    )

    # ── Build display DataFrame ────────────────────────────────────────────
    rows = []
    for r in sim_rows:
        gain = r["gain_loss"]
        gain_pct = r["gain_loss_pct"]
        adv = r["compound_advantage"]
        adv_str = (
            f"+{_fmt_currency(adv, sym)}" if adv >= 0.005
            else _fmt_currency(adv, sym)
        )
        rows.append(
            {
                "Plazo": r["label"],
                "Valor Proyectado (Compuesto)": _fmt_currency(r["projected_value"], sym),
                "Ganancia / Pérdida": _fmt_currency(abs(gain), ("+" if gain >= 0 else "-") + sym),
                "Variación %": _fmt_pct(gain_pct),
                "Extra vs. Interés Simple": adv_str,
                "Optimista": _fmt_currency(r["optimistic_value"], sym),
                "Pesimista": _fmt_currency(r["pessimistic_value"], sym),
                "_gain_raw": gain,
                "_adv_raw": adv,
            }
        )

    display_df = pd.DataFrame(rows)
    display_cols = [
        "Plazo", "Valor Proyectado (Compuesto)", "Ganancia / Pérdida",
        "Variación %", "Extra vs. Interés Simple", "Optimista", "Pesimista",
    ]
    gain_raw_values = display_df["_gain_raw"].tolist()
    adv_raw_values = display_df["_adv_raw"].tolist()

    def _style_col(col):
        if col.name in ("Ganancia / Pérdida", "Variación %"):
            return [
                f"color: {'#00C805' if gain_raw_values[i] >= 0 else '#FF3131'}; font-weight:600;"
                for i in range(len(col))
            ]
        if col.name == "Extra vs. Interés Simple":
            return [
                f"color: #00C805; font-weight:600;"
                for _ in range(len(col))
            ]
        return [""] * len(col)

    styled = (
        display_df[display_cols]
        .style
        .apply(_style_col, axis=0)
        .set_properties(**{"text-align": "right"}, subset=display_cols[1:])
        .set_properties(**{"font-weight": "700"}, subset=["Plazo"])
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Compound interest explainer ────────────────────────────────────────
    cagr_pct_val = hist["cagr"] * 100
    example_amount = 10_000
    example_years = 10
    example_compound = example_amount * ((1 + hist["cagr"]) ** example_years)
    example_simple = example_amount * (1 + hist["cagr"] * example_years)
    with st.expander("¿Cómo funciona el interés compuesto?", expanded=False):
        st.markdown(
            f"**Interés simple:** cada año ganas el mismo monto sobre tu capital inicial. "
            f"Con {sym}{example_amount:,.0f} al {cagr_pct_val:.1f}% anual, "
            f"ganas {sym}{example_amount * hist['cagr']:,.0f} cada año.\n\n"
            f"**Interés compuesto:** cada año ganas sobre tu capital inicial "
            f"*más* todas las ganancias acumuladas. Esas ganancias también generan ganancias.\n\n"
            f"**Ejemplo concreto** con {sym}{example_amount:,.0f} al {cagr_pct_val:.1f}% en {example_years} años:\n"
            f"- Interés simple → {sym}{example_simple:,.0f}\n"
            f"- Interés compuesto → {sym}{example_compound:,.0f}\n"
            f"- **Ventaja del compuesto: {sym}{example_compound - example_simple:,.0f} extra**"
        )

    # ── Disclaimer ─────────────────────────────────────────────────────────
    st.caption(get_simulation_disclaimer())
