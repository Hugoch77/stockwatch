"""
StockWatch Rankings
-------------------
Computes top-performing stocks/ETFs by historical CAGR.
Only assets with at least `min_years` of data are included.

Uses the in-memory OHLCV cache from data/fetcher.py, so the first call
fetches all tickers from the network (10–30 s); subsequent calls are fast.
"""

import math
import logging
from typing import Optional

from data.fetcher import get_ohlcv
from data.search import MX_STOCKS, US_STOCKS, MX_ETFS, US_ETFS
from analysis.simulator import calculate_historical_returns

logger = logging.getLogger(__name__)

# ── In-memory result cache ─────────────────────────────────────────────────
_rankings_cache: dict = {}
_cache_ttl: int = 3600  # 1 hour


def build_ticker_meta_list() -> list[dict]:
    """
    Build a flat list of ticker metadata from the four static dicts in search.py.

    Returns
    -------
    list of dicts, each with: ticker, name, asset_type, market
    """
    entries = []

    # MX_STOCKS — values: (name, asset_type, exchange)
    for ticker, (name, _asset_type, _exchange) in MX_STOCKS.items():
        entries.append({
            "ticker": ticker,
            "name": name or ticker,
            "asset_type": "Acción",
            "market": "MX",
        })

    # US_STOCKS
    for ticker, (name, _asset_type, _exchange) in US_STOCKS.items():
        entries.append({
            "ticker": ticker,
            "name": name or ticker,
            "asset_type": "Acción",
            "market": "US",
        })

    # MX_ETFS
    for ticker, (name, _asset_type, _exchange) in MX_ETFS.items():
        entries.append({
            "ticker": ticker,
            "name": name or ticker,
            "asset_type": "ETF",
            "market": "MX",
        })

    # US_ETFS
    for ticker, (name, _asset_type, _exchange) in US_ETFS.items():
        entries.append({
            "ticker": ticker,
            "name": name or ticker,
            "asset_type": "ETF",
            "market": "US",
        })

    return entries


def get_rankings_count() -> int:
    """Return the total number of tickers in the static dicts (for UI progress estimation)."""
    return len(MX_STOCKS) + len(US_STOCKS) + len(MX_ETFS) + len(US_ETFS)


def get_top_performers(
    tickers_with_meta: list[dict],
    min_years: int = 15,
    top_n: int = 10,
) -> list[dict]:
    """
    Compute top-performing tickers by historical CAGR.

    Parameters
    ----------
    tickers_with_meta : list of dicts — each must have: ticker, name, asset_type, market
    min_years         : int  — minimum years of history required (default 15)
    top_n             : int  — number of top results to return (default 10)

    Returns
    -------
    list of dicts (up to top_n), sorted by CAGR descending, each containing:
        ticker, name, cagr, cagr_pct, data_years, asset_type, market,
        volatility, best_year, worst_year, rank
    """
    qualifying: list[dict] = []

    for meta in tickers_with_meta:
        ticker = meta.get("ticker", "")
        name = meta.get("name", ticker)
        asset_type = meta.get("asset_type", "Acción")
        market = meta.get("market", "US")

        try:
            ohlcv = get_ohlcv(ticker, period="max")
            if ohlcv is None:
                logger.debug("Rankings: no OHLCV data for %s — skipped", ticker)
                continue

            df = ohlcv.df
            if df is None or len(df) < 2:
                logger.debug("Rankings: insufficient rows for %s — skipped", ticker)
                continue

            stats = calculate_historical_returns(df)

            data_years = stats.get("data_years", 0.0)
            if data_years < min_years:
                logger.debug(
                    "Rankings: %s has %.1f years (< %d required) — skipped",
                    ticker, data_years, min_years,
                )
                continue

            cagr = stats.get("cagr", 0.0)
            # Skip tickers where CAGR is NaN or non-finite
            if cagr is None or not math.isfinite(cagr):
                logger.debug("Rankings: non-finite CAGR for %s — skipped", ticker)
                continue

            qualifying.append({
                "ticker": ticker,
                "name": name,
                "cagr": cagr,
                "cagr_pct": round(cagr * 100, 2),
                "data_years": data_years,
                "asset_type": asset_type,
                "market": market,
                "volatility": stats.get("volatility", 0.0),
                "best_year": stats.get("best_year", 0.0),
                "worst_year": stats.get("worst_year", 0.0),
            })

        except Exception as exc:
            logger.warning("Rankings: error processing %s — %s", ticker, exc)
            continue

    # Sort by CAGR descending
    qualifying.sort(key=lambda x: x["cagr"], reverse=True)

    # Slice top_n and add 1-based rank
    top = qualifying[:top_n]
    for i, entry in enumerate(top, start=1):
        entry["rank"] = i

    return top


def get_rankings_cached(min_years: int = 15, top_n: int = 10) -> list[dict]:
    """
    Cached wrapper for get_top_performers().

    Results are kept in a module-level dict with a 1-hour TTL so Streamlit
    re-runs don't recompute rankings on every interaction.

    Parameters
    ----------
    min_years : int — minimum years of history required (default 15)
    top_n     : int — number of top results to return (default 10)

    Returns
    -------
    list of dicts — same format as get_top_performers()
    """
    import time

    key = f"{min_years}_{top_n}"
    now = time.time()

    if key in _rankings_cache:
        result, cached_at = _rankings_cache[key]
        if now - cached_at < _cache_ttl:
            return result

    result = get_top_performers(build_ticker_meta_list(), min_years=min_years, top_n=top_n)
    _rankings_cache[key] = (result, now)
    return result
