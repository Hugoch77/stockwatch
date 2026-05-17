"""
StockWatch Ticker Search
------------------------
Search by ticker symbol or company name using:
1. Static dictionary fallback (popular MX + US stocks)
2. yfinance.Search (yfinance >= 0.2.38) — returns matching tickers
"""
import yfinance as yf
import logging
from typing import List
from data.models import SearchResult

logger = logging.getLogger(__name__)

# Popular MX stocks
MX_STOCKS = {
    "AMXL.MX": ("América Móvil", "Acción", "BMV"),
    "GFNORTEO.MX": ("Grupo Financiero Banorte", "Acción", "BMV"),
    "WALMEX*.MX": ("Walmart de México", "Acción", "BMV"),
    "FEMSAUBD.MX": ("FEMSA", "Acción", "BMV"),
    "CEMEXCPO.MX": ("CEMEX", "Acción", "BMV"),
    "BIMBOA.MX": ("Grupo Bimbo", "Acción", "BMV"),
    "ALSEA*.MX": ("Alsea", "Acción", "BMV"),
    "KOFUBL.MX": ("Coca-Cola FEMSA", "Acción", "BMV"),
    "GMEXICOB.MX": ("Grupo México", "Acción", "BMV"),
    "PINFRA*.MX": ("Promotora y Operadora de Infraestructura", "Acción", "BMV"),
    "GRUMAB.MX": ("Gruma", "Acción", "BMV"),
    "AC*.MX": ("Arca Continental", "Acción", "BMV"),
    "ALPEKA.MX": ("Alpek", "Acción", "BMV"),
    "ASURB.MX": ("Grupo Aeroportuario del Sureste", "Acción", "BMV"),
    "OMAB.MX": ("Grupo Aeroportuario del Centro Norte", "Acción", "BMV"),
    "GAPB.MX": ("Grupo Aeroportuario del Pacífico", "Acción", "BMV"),
    "SANMEXB.MX": ("Banco Santander México", "Acción", "BMV"),
    "CUERVO.MX": ("José Cuervo", "Acción", "BMV"),
    "LIVEPOLC-1.MX": ("El Puerto de Liverpool", "Acción", "BMV"),
    "ORBIA*.MX": ("Orbia Advance Corporation", "Acción", "BMV"),
    "ELEKTRA*.MX": ("Grupo Elektra", "Acción", "BMV"),
    "SORIANAB.MX": ("Organización Soriana", "Acción", "BMV"),
    "AXTELCPO.MX": ("Axtel", "Acción", "BMV"),
    "IENOVA*.MX": ("IEnova", "Acción", "BMV"),
}

# Popular MX ETFs / FIBRAs
MX_ETFS = {
    "NAFTRACISHRS.MX": ("NAFTRAC iShares S&P/BMV IPC ETF", "ETF", "BMV"),
    "FUNO11.MX": ("Fibra Uno (FIBRA/REIT)", "ETF", "BMV"),
    "FIBRAMQ12.MX": ("FIBRA Macquarie México", "ETF", "BMV"),
    "BSMXIB.MX": ("BlackRock México Bolsa ETF", "ETF", "BMV"),
    "MEXTRAC.MX": ("MEXTRAC iShares MSCI México ETF", "ETF", "BMV"),
}

US_STOCKS = {
    "AAPL": ("Apple Inc.", "Acción", "NASDAQ"),
    "MSFT": ("Microsoft Corporation", "Acción", "NASDAQ"),
    "GOOGL": ("Alphabet Inc. (Google)", "Acción", "NASDAQ"),
    "AMZN": ("Amazon.com Inc.", "Acción", "NASDAQ"),
    "NVDA": ("NVIDIA Corporation", "Acción", "NASDAQ"),
    "META": ("Meta Platforms Inc.", "Acción", "NASDAQ"),
    "TSLA": ("Tesla Inc.", "Acción", "NASDAQ"),
    "BRK-B": ("Berkshire Hathaway Inc.", "Acción", "NYSE"),
    "JPM": ("JPMorgan Chase & Co.", "Acción", "NYSE"),
    "JNJ": ("Johnson & Johnson", "Acción", "NYSE"),
    "V": ("Visa Inc.", "Acción", "NYSE"),
    "PG": ("Procter & Gamble Co.", "Acción", "NYSE"),
    "XOM": ("Exxon Mobil Corporation", "Acción", "NYSE"),
}

# Popular US ETFs
US_ETFS = {
    "SPY": ("SPDR S&P 500 ETF", "ETF", "NYSE"),
    "QQQ": ("Invesco QQQ Trust (Nasdaq 100)", "ETF", "NASDAQ"),
    "IVV": ("iShares Core S&P 500 ETF", "ETF", "NYSE"),
    "VOO": ("Vanguard S&P 500 ETF", "ETF", "NYSE"),
    "VTI": ("Vanguard Total Stock Market ETF", "ETF", "NYSE"),
    "GLD": ("SPDR Gold Shares", "ETF", "NYSE"),
    "TLT": ("iShares 20+ Year Treasury Bond ETF", "ETF", "NASDAQ"),
    "VNQ": ("Vanguard Real Estate ETF", "ETF", "NYSE"),
    "EWW": ("iShares MSCI Mexico ETF", "ETF", "NYSE"),
    "VWO": ("Vanguard FTSE Emerging Markets ETF", "ETF", "NYSE"),
    "ARKK": ("ARK Innovation ETF", "ETF", "NYSE"),
}

# Merged lookup for static search
_ALL_STOCKS = {}
_ALL_STOCKS.update({k: (*v, "MX") for k, v in MX_STOCKS.items()})
_ALL_STOCKS.update({k: (*v, "MX") for k, v in MX_ETFS.items()})
_ALL_STOCKS.update({k: (*v, "US") for k, v in US_STOCKS.items()})
_ALL_STOCKS.update({k: (*v, "US") for k, v in US_ETFS.items()})


def _static_search(query: str) -> List[SearchResult]:
    """Search static dictionaries by ticker prefix or name substring (case-insensitive)."""
    q = query.upper()
    q_lower = query.lower()
    results = []

    for ticker, (name, asset_type, exchange, market) in _ALL_STOCKS.items():
        ticker_match = ticker.upper().startswith(q)
        name_match = q_lower in name.lower()
        if ticker_match or name_match:
            results.append(SearchResult(
                ticker=ticker,
                name=name,
                market=market,
                asset_type=asset_type,
                exchange=exchange,
            ))

    return results


def _yfinance_search(query: str) -> List[SearchResult]:
    """Search using yfinance.Search API. Returns results or empty list on error."""
    try:
        search = yf.Search(query)
        quotes = getattr(search, "quotes", [])
        if not quotes:
            return []

        results = []
        seen = set()
        for q in quotes:
            symbol = q.get("symbol", "")
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)

            name = q.get("longname") or q.get("shortname") or q.get("longName") or q.get("shortName") or symbol
            exchange = q.get("exchDisp") or q.get("exchange") or ""
            quote_type = q.get("quoteType", "")

            asset_type = "ETF" if quote_type in ("ETF", "MUTUALFUND") else "Acción"
            market = "MX" if symbol.upper().endswith(".MX") else "US"

            results.append(SearchResult(
                ticker=symbol,
                name=name,
                market=market,
                asset_type=asset_type,
                exchange=exchange,
            ))

        return results

    except Exception as e:
        logger.debug("yfinance Search failed for '%s': %s", query, e)
        return []


def search_tickers(query: str, limit: int = 10, market: str = None) -> List[SearchResult]:
    """
    Search for tickers by name or symbol.
    Strategy:
    1. First check static dictionaries (case-insensitive partial match on ticker or name)
    2. Then try yfinance.Search(query) for additional live results
    3. Return combined, deduplicated results up to `limit`

    Args:
        query: Ticker symbol or company name to search.
        limit: Maximum number of results to return.
        market: Optional filter — 'US', 'MX', or None for all markets.
    """
    if not query or not query.strip():
        return []

    query = query.strip()

    # Static results first (instant, no network)
    static_results = _static_search(query)

    # Live results from yfinance
    live_results = _yfinance_search(query)

    # Merge and deduplicate — static results take priority
    seen_tickers = set()
    combined = []

    for r in static_results:
        key = r.ticker.upper()
        if key not in seen_tickers:
            seen_tickers.add(key)
            combined.append(r)

    for r in live_results:
        key = r.ticker.upper()
        if key not in seen_tickers:
            seen_tickers.add(key)
            combined.append(r)

    # Apply market filter if provided
    if market:
        combined = [r for r in combined if r.market == market]

    return combined[:limit]


def validate_ticker(ticker: str) -> bool:
    """
    Returns True if the ticker is valid (yfinance can fetch it).
    Quick check: try fetching .fast_info. Returns False on error.
    """
    if not ticker or not ticker.strip():
        return False
    try:
        t = yf.Ticker(ticker.strip())
        fi = t.fast_info
        # fast_info should have a market price if the ticker is valid
        return fi is not None and hasattr(fi, "last_price") and fi.last_price is not None
    except Exception:
        return False
