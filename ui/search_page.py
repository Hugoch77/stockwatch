"""
Search Page — Landing page of StockWatch.
User types a ticker or company name, sees results, and navigates to detail.
Two tabs: Acciones and ETFs.
"""
import streamlit as st
from typing import Optional
from ui.components import render_signal_badge, format_number

try:
    from analysis.rankings import get_rankings_cached
    _RANKINGS_AVAILABLE = True
except ImportError:
    _RANKINGS_AVAILABLE = False

try:
    from data.fetcher import get_ohlcv
    import ta
    _RSI_AVAILABLE = True
except ImportError:
    _RSI_AVAILABLE = False

# ── RSI cache ─────────────────────────────────────────────────────────────────
_rsi_cache: dict = {}
_rsi_cache_ttl: int = 300  # 5 minutes

# ── RSI Buy Opportunities cache ───────────────────────────────────────────────
_rsi_buy_cache: dict = {}
_rsi_buy_cache_ttl: int = 300  # 5 minutes


def _get_rsi_for_ticker(ticker: str) -> dict:
    """Fetch current RSI(14) for a ticker. Returns dict with value, zone, signal."""
    if not _RSI_AVAILABLE:
        return {"value": None, "zone": "N/D", "signal": "—"}
    try:
        ohlcv = get_ohlcv(ticker, period="3mo")
        if ohlcv is None:
            return {"value": None, "zone": "N/D", "signal": "—"}
        df = ohlcv.df if hasattr(ohlcv, "df") else ohlcv
        if df is None or df.empty:
            return {"value": None, "zone": "N/D", "signal": "—"}
        rsi_series = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
        rsi_clean = rsi_series.dropna()
        if rsi_clean.empty:
            return {"value": None, "zone": "N/D", "signal": "—"}
        rsi = float(rsi_clean.iloc[-1])
        if rsi >= 70:
            zone, signal = "Sobrecompra", "⚠️ Vender"
        elif rsi <= 30:
            zone, signal = "Sobreventa", "✅ Comprar"
        elif rsi >= 50:
            zone, signal = "Alcista", "🟡 Mantener"
        else:
            zone, signal = "Bajista", "🟡 Mantener"
        return {"value": round(rsi, 1), "zone": zone, "signal": signal}
    except Exception:
        return {"value": None, "zone": "N/D", "signal": "—"}


def _get_rsi_cached(ticker: str) -> dict:
    """Return cached RSI data for a ticker, refreshing after _rsi_cache_ttl seconds."""
    import time
    now = time.time()
    if ticker in _rsi_cache:
        result, cached_at = _rsi_cache[ticker]
        if now - cached_at < _rsi_cache_ttl:
            return result
    result = _get_rsi_for_ticker(ticker)
    _rsi_cache[ticker] = (result, now)
    return result


def _get_rsi_buy_opportunities(top_n: int = 10, rsi_threshold: float = 35.0) -> list:
    """
    Scan all tickers and return those with RSI <= rsi_threshold,
    sorted by RSI ascending (most oversold first).
    """
    if not _RSI_AVAILABLE:
        return []

    try:
        from analysis.rankings import build_ticker_meta_list
        all_tickers = build_ticker_meta_list()
    except Exception:
        return []

    opportunities = []
    for meta in all_tickers:
        ticker = meta.get("ticker", "")
        name = meta.get("name", ticker)
        asset_type = meta.get("asset_type", "Acción")
        market = meta.get("market", "US")

        rsi_data = _get_rsi_cached(ticker)
        rsi_val = rsi_data.get("value")

        if rsi_val is None:
            continue
        if rsi_val > rsi_threshold:
            continue

        opportunities.append({
            "ticker": ticker,
            "name": name,
            "asset_type": asset_type,
            "market": market,
            "rsi_value": rsi_val,
            "rsi_zone": rsi_data.get("zone", "Sobreventa"),
            "signal": rsi_data.get("signal", "✅ Comprar"),
        })

    # Sort by RSI ascending (most oversold = best buy signal = lowest RSI first)
    opportunities.sort(key=lambda x: x["rsi_value"])

    # Add rank
    for i, item in enumerate(opportunities[:top_n], start=1):
        item["rank"] = i

    return opportunities[:top_n]


def _get_rsi_buy_opportunities_cached(top_n: int = 10, rsi_threshold: float = 35.0) -> list:
    """Return cached RSI buy opportunities, refreshing after _rsi_buy_cache_ttl seconds."""
    import time
    key = f"{top_n}_{rsi_threshold}"
    now = time.time()
    if key in _rsi_buy_cache:
        result, cached_at = _rsi_buy_cache[key]
        if now - cached_at < _rsi_buy_cache_ttl:
            return result
    result = _get_rsi_buy_opportunities(top_n=top_n, rsi_threshold=rsi_threshold)
    _rsi_buy_cache[key] = (result, now)
    return result


# ── Popular quick-access tickers ─────────────────────────────────────────────

POPULAR_MX_STOCKS = [
    ("AMX.MX", "América Móvil"),
    ("WALMEX.MX", "Walmart México"),
    ("CEMEX.MX", "Cemex"),
    ("GFNORTE.MX", "Banorte"),
    ("BIMBO.MX", "Bimboa"),
    ("TLEVISA.MX", "Televisa"),
    ("FEMSAUBD.MX", "FEMSA"),
    ("AC.MX", "Arca Continental"),
]

POPULAR_US_STOCKS = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("GOOGL", "Alphabet"),
    ("AMZN", "Amazon"),
    ("TSLA", "Tesla"),
    ("NVDA", "NVIDIA"),
    ("META", "Meta"),
    ("JPM", "JPMorgan"),
]

POPULAR_MX_ETFS = [
    ("NAFTRACISHRS.MX", "NAFTRAC"),
    ("FUNO11.MX", "Fibra Uno"),
    ("FIBRAMQ12.MX", "FIBRA MQ"),
    ("BSMXIB.MX", "BlackRock MX"),
]

POPULAR_US_ETFS = [
    ("SPY", "S&P 500 ETF"),
    ("QQQ", "Nasdaq 100 ETF"),
    ("IVV", "iShares S&P 500"),
    ("VOO", "Vanguard S&P 500"),
    ("GLD", "SPDR Gold"),
    ("TLT", "Bonos 20+ años"),
    ("EWW", "México ETF (US)"),
    ("VTI", "Total Market ETF"),
]


def _render_top10() -> None:
    """Render the Top 10 Best Historical Performance section."""
    with st.expander("🏆 Top 10 — Mejor Rendimiento Histórico (≥15 años de datos)", expanded=True):
        if not _RANKINGS_AVAILABLE:
            st.info("Módulo de rankings no disponible aún.")
            return

        with st.spinner("Calculando rendimientos históricos e indicadores RSI... (puede tardar hasta 30 segundos la primera vez)"):
            try:
                rankings = get_rankings_cached(min_years=15, top_n=10)
            except Exception as e:
                st.warning(f"No se pudieron cargar los rankings: {e}")
                rankings = []

            # Build rows with RSI inside the spinner so user sees progress
            import pandas as pd

            rows = []
            for r in rankings:
                flag = "🇲🇽" if r.get("market") == "MX" else "🇺🇸"
                tipo = "🟢 Acción" if r.get("asset_type") == "Acción" else "🔵 ETF"
                cagr = r.get("cagr_pct", 0.0)
                vol = r.get("volatility", 0.0)
                years = r.get("data_years", 0.0)

                rsi_data = _get_rsi_cached(r.get("ticker", ""))
                rsi_val = rsi_data.get("value")
                rsi_zone = rsi_data.get("zone", "N/D")
                rsi_signal = rsi_data.get("signal", "—")
                rsi_display = f"{rsi_val} — {rsi_zone}" if rsi_val is not None else "N/D"

                rows.append({
                    "Pos.": r.get("rank", ""),
                    "Ticker": r.get("ticker", ""),
                    "Nombre": r.get("name", ""),
                    "Tipo": tipo,
                    "Mercado": flag,
                    "CAGR Anual": f"+{cagr:.2f}%",
                    "Volatilidad": f"{vol * 100:.1f}%",
                    "Años de datos": f"{years:.1f} años",
                    "RSI (14)": rsi_display,
                    "Señal RSI": rsi_signal,
                })

        df = pd.DataFrame(rows)

        if not rankings:
            st.info("No hay suficientes datos para calcular el ranking.")
            return

        count = len(rankings)
        if count < 10:
            st.caption(f"Mostrando {count} instrumentos con ≥15 años de datos")

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Navigation buttons — one per ticker
        st.markdown("**Ver análisis detallado:**")
        btn_cols = st.columns(min(len(rankings), 5))
        for i, r in enumerate(rankings):
            ticker = r.get("ticker", "")
            with btn_cols[i % 5]:
                if st.button(f"📊 {ticker}", key=f"top10_btn_{ticker}", use_container_width=True):
                    _navigate_to_detail(ticker)
                    st.rerun()

        st.caption(
            "🔄 Rankings actualizados cada hora. "
            "Basados en rendimientos históricos de los instrumentos en la lista de búsqueda con al menos 15 años de datos."
        )


def _render_rsi_buy_top10() -> None:
    """Render Top 10 RSI buy opportunities section."""
    with st.expander("✅ Top 10 — Mejores Oportunidades de Compra (RSI ≤ 35)", expanded=True):
        if not _RSI_AVAILABLE:
            st.info("Módulo RSI no disponible.")
            return

        with st.spinner("Escaneando señales RSI de todos los instrumentos..."):
            try:
                opportunities = _get_rsi_buy_opportunities_cached(top_n=10, rsi_threshold=35.0)
            except Exception as e:
                st.warning(f"No se pudieron calcular las oportunidades RSI: {e}")
                opportunities = []

        if not opportunities:
            st.info("🟡 Ningún instrumento en zona de sobreventa (RSI ≤ 35) en este momento. El mercado no muestra señales de compra por RSI actualmente.")
            st.caption("🔄 Esta sección se actualiza cada 5 minutos. Vuelve más tarde.")
            return

        count = len(opportunities)
        st.markdown(f"**{count} instrumento{'s' if count != 1 else ''} en zona de Sobreventa** — ordenados del RSI más bajo al más alto.")

        import pandas as pd
        rows = []
        for r in opportunities:
            flag = "🇲🇽" if r.get("market") == "MX" else "🇺🇸"
            tipo = "🟢 Acción" if r.get("asset_type") == "Acción" else "🔵 ETF"
            rsi_val = r.get("rsi_value", 0)
            rows.append({
                "Pos.": r.get("rank", ""),
                "Ticker": r.get("ticker", ""),
                "Nombre": r.get("name", ""),
                "Tipo": tipo,
                "Mercado": flag,
                "RSI (14)": f"{rsi_val:.1f}",
                "Zona": r.get("rsi_zone", "Sobreventa"),
                "Señal": r.get("signal", "✅ Comprar"),
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Navigation buttons
        st.markdown("**Ver análisis detallado:**")
        btn_cols = st.columns(min(len(opportunities), 5))
        for i, r in enumerate(opportunities):
            ticker = r.get("ticker", "")
            with btn_cols[i % 5]:
                if st.button(f"📊 {ticker}", key=f"rsi_buy_btn_{ticker}", use_container_width=True):
                    _navigate_to_detail(ticker)
                    st.rerun()

        st.caption(
            "📊 RSI ≤ 30: zona de sobreventa clásica (señal fuerte). RSI 30–35: zona de sobreventa extendida (señal moderada). "
            "⚠️ El RSI es un indicador técnico — no garantiza rendimientos futuros. Úsalo junto con análisis fundamental."
        )


def _navigate_to_detail(ticker: str) -> None:
    """Set session state and navigate to detail page."""
    st.session_state.selected_ticker = ticker
    st.session_state.page = "detail"


def _type_badge_html(asset_type: str) -> str:
    """Return a small inline HTML badge for the asset type."""
    if asset_type == "ETF":
        return (
            "<span style='background:#1a3a5c; color:#4fc3f7; padding:1px 7px; "
            "border-radius:4px; font-size:0.78rem; font-weight:600;'>🔵 ETF</span>"
        )
    return (
        "<span style='background:#1a3a1a; color:#66bb6a; padding:1px 7px; "
        "border-radius:4px; font-size:0.78rem; font-weight:600;'>🟢 Acción</span>"
    )


def _do_search(query: str, market_code: Optional[str], asset_type_filter: str) -> list:
    """Run search and return results filtered to the requested asset_type."""
    try:
        from data.search import search_tickers
        # Fetch more than the default so filtering still yields good results
        results = search_tickers(query, limit=40, market=market_code)
    except ImportError:
        results = _fallback_search(query, asset_type_filter)
    except Exception as e:
        st.warning(f"Error en la búsqueda: {e}")
        return []
    return [r for r in results if (r.asset_type if hasattr(r, "asset_type") else r.get("asset_type", "")) == asset_type_filter]


def _render_results(results: list, key_prefix: str) -> None:
    """Render a list of SearchResult objects as clickable cards with type badges."""
    if not results:
        st.info("No se encontraron resultados. Intenta con otro término.")
        return

    st.markdown(f"### Resultados ({len(results)})")
    for result in results[:20]:
        ticker = result.ticker if hasattr(result, "ticker") else result.get("ticker", "")
        name = result.name if hasattr(result, "name") else result.get("name", "")
        market = result.market if hasattr(result, "market") else result.get("market", "")
        asset_type = result.asset_type if hasattr(result, "asset_type") else result.get("asset_type", "")
        flag = "🇲🇽" if market == "MX" else "🇺🇸"
        badge = _type_badge_html(asset_type)

        col_info, col_btn = st.columns([4, 1])
        with col_info:
            st.markdown(
                f"**{ticker}** — {name} &nbsp; {flag} &nbsp; {badge}",
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("Ver →", key=f"{key_prefix}_{ticker}", use_container_width=True):
                _navigate_to_detail(ticker)
                st.rerun()


def _render_popular_buttons(popular_list: list, key_prefix: str) -> None:
    """Render a row of quick-access ticker buttons."""
    cols = st.columns(4)
    for i, (ticker, name) in enumerate(popular_list):
        with cols[i % 4]:
            if st.button(f"{ticker}\n{name}", key=f"{key_prefix}_{ticker}", use_container_width=True):
                _navigate_to_detail(ticker)
                st.rerun()


def render_search_page() -> None:
    """Render the search / landing page."""
    st.markdown("# 🔍 Buscar Acciones y ETFs")
    st.caption("Selecciona una pestaña, escribe un ticker o nombre para analizar.")

    # ── Top 10 Rankings ──────────────────────────────────────────────────────
    _render_top10()

    # ── RSI Buy Opportunities ─────────────────────────────────────────────────
    _render_rsi_buy_top10()

    # ── Market filter (shared above tabs) ────────────────────────────────────
    market_filter = st.radio(
        "Mercado",
        ["Todos", "🇺🇸 USA", "🇲🇽 México"],
        horizontal=True,
        key="market_filter",
        label_visibility="collapsed",
    )
    market_code: Optional[str] = None
    if market_filter == "🇺🇸 USA":
        market_code = "US"
    elif market_filter == "🇲🇽 México":
        market_code = "MX"

    show_mx = market_filter in ("Todos", "🇲🇽 México")
    show_us = market_filter in ("Todos", "🇺🇸 USA")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_acciones, tab_etfs = st.tabs(["📈 Acciones", "🏦 ETFs"])

    # ── Tab: Acciones ─────────────────────────────────────────────────────────
    with tab_acciones:
        query_acc = st.text_input(
            "Buscar acción",
            placeholder="Ticker o empresa (ej: AAPL, América Móvil)",
            key="search_acciones",
            label_visibility="collapsed",
        )

        if not query_acc or len(query_acc) < 2:
            if show_mx:
                st.markdown("### 🇲🇽 Acciones populares — México")
                _render_popular_buttons(POPULAR_MX_STOCKS, "pop_acc_mx")
            if show_us:
                st.markdown("### 🇺🇸 Acciones populares — USA")
                _render_popular_buttons(POPULAR_US_STOCKS, "pop_acc_us")
        else:
            with st.spinner("Buscando acciones..."):
                results = _do_search(query_acc, market_code, "Acción")
            _render_results(results, "res_acc")

    # ── Tab: ETFs ─────────────────────────────────────────────────────────────
    with tab_etfs:
        query_etf = st.text_input(
            "Buscar ETF",
            placeholder="Ticker o fondo (ej: SPY, NAFTRAC, QQQ)",
            key="search_etfs",
            label_visibility="collapsed",
        )

        if not query_etf or len(query_etf) < 2:
            if show_mx:
                st.markdown("### 🇲🇽 ETFs populares — México / FIBRAs")
                _render_popular_buttons(POPULAR_MX_ETFS, "pop_etf_mx")
            if show_us:
                st.markdown("### 🇺🇸 ETFs populares — USA")
                _render_popular_buttons(POPULAR_US_ETFS, "pop_etf_us")
        else:
            with st.spinner("Buscando ETFs..."):
                results = _do_search(query_etf, market_code, "ETF")
            _render_results(results, "res_etf")


def _fallback_search(query: str, asset_type_filter: str):
    """Fallback: if data.search isn't available, let user enter ticker directly."""
    st.info(
        "El módulo de búsqueda no está disponible. "
        "Puedes escribir el ticker exacto y presionar Enter."
    )

    class _FakeResult:
        def __init__(self, t):
            self.ticker = t.upper().strip()
            self.name = t.upper().strip()
            self.market = "MX" if ".MX" in t.upper() else "US"
            self.asset_type = asset_type_filter
            self.exchange = ""

    q = query.strip()
    if q:
        return [_FakeResult(q)]
    return []

