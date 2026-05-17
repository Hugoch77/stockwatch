"""
StockWatch Data Fetcher
-----------------------
Wraps yfinance with TTL caching and error handling.

US stocks: AAPL, MSFT, SPY, QQQ, etc. (no suffix)
Mexican stocks (BMV): AMXL.MX, GFNORTEO.MX, CEMEXCPO.MX, etc. (.MX suffix)
"""
import yfinance as yf
import pandas as pd
import threading
import time
import logging
from typing import Optional, Dict, Tuple, Any
from data.models import StockInfo, OHLCVData

logger = logging.getLogger(__name__)

# Cache entry: (value, expiry_timestamp)
_cache: Dict[str, Tuple[Any, float]] = {}
_cache_lock = threading.Lock()

CACHE_TTL_QUOTE = 60
CACHE_TTL_OHLCV = 300
CACHE_TTL_INFO = 3600


def _get_cache(key: str) -> Optional[Any]:
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() < entry[1]:
            return entry[0]
    return None


def _set_cache(key: str, value: Any, ttl: int) -> None:
    with _cache_lock:
        _cache[key] = (value, time.time() + ttl)


def detect_market(ticker: str) -> str:
    """Returns 'MX' if ticker ends with .MX, else 'US'."""
    return "MX" if ticker.upper().endswith(".MX") else "US"


def _safe_get(info: dict, key: str, default=None):
    """Safely get a value from the info dict, returning default if missing or None."""
    val = info.get(key)
    return val if val is not None else default


def get_stock_info(ticker: str) -> Optional[StockInfo]:
    """
    Fetch snapshot + fundamental data for a ticker.
    Returns None if ticker not found or fetch fails.
    """
    cache_key = f"info:{ticker}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            # Try to get at least a price from history as last resort
            hist = t.history(period="5d")
            if hist.empty:
                logger.warning("No data found for ticker %s", ticker)
                return None
            last_close = float(hist["Close"].dropna().iloc[-1])
            price = last_close
        else:
            price = _safe_get(info, "currentPrice") or _safe_get(info, "regularMarketPrice")
            if price is None:
                hist = t.history(period="5d")
                if hist.empty:
                    logger.warning("No price data for ticker %s", ticker)
                    return None
                price = float(hist["Close"].dropna().iloc[-1])

        market = detect_market(ticker)
        currency = _safe_get(info, "currency", "MXN" if market == "MX" else "USD")

        name = _safe_get(info, "longName") or _safe_get(info, "shortName") or ticker

        change = _safe_get(info, "regularMarketChange", 0.0)
        change_pct = _safe_get(info, "regularMarketChangePercent", 0.0)
        volume = int(_safe_get(info, "regularMarketVolume", 0) or 0)
        avg_volume = int(_safe_get(info, "averageVolume", 0) or 0)

        # Dividend yield: yfinance returns as decimal (e.g. 0.015 = 1.5%)
        raw_div_yield = _safe_get(info, "dividendYield")
        dividend_yield = round(raw_div_yield * 100, 4) if raw_div_yield is not None else None

        # ETF-specific fields
        quote_type = _safe_get(info, "quoteType", "")
        is_etf = quote_type in ("ETF", "MUTUALFUND")
        expense_ratio = None
        category = None
        if is_etf:
            expense_ratio = _safe_get(info, "annualReportExpenseRatio") or _safe_get(info, "totalExpenseRatio")
            category = _safe_get(info, "category")

        result = StockInfo(
            ticker=ticker,
            name=name,
            market=market,
            currency=currency,
            price=float(price),
            change=float(change),
            change_pct=float(change_pct),
            volume=volume,
            avg_volume=avg_volume,
            market_cap=_safe_get(info, "marketCap"),
            pe_ratio=_safe_get(info, "trailingPE"),
            eps=_safe_get(info, "trailingEps"),
            dividend_yield=dividend_yield,
            dividend_rate=_safe_get(info, "dividendRate"),
            week_52_high=float(_safe_get(info, "fiftyTwoWeekHigh", 0.0) or 0.0),
            week_52_low=float(_safe_get(info, "fiftyTwoWeekLow", 0.0) or 0.0),
            beta=_safe_get(info, "beta"),
            sector=_safe_get(info, "sector"),
            industry=_safe_get(info, "industry"),
            description=_safe_get(info, "longBusinessSummary"),
            expense_ratio=expense_ratio,
            category=category,
            asset_type="ETF" if is_etf else "Acción",
        )

        _set_cache(cache_key, result, CACHE_TTL_INFO)
        return result

    except Exception as e:
        logger.warning("Failed to fetch info for %s: %s", ticker, e)
        return None


def get_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> Optional[OHLCVData]:
    """
    Fetch OHLCV history using yf.Ticker(ticker).history().
    Returns OHLCVData with cleaned DataFrame (no NaN rows, sorted ascending by date).
    """
    cache_key = f"ohlcv:{ticker}:{period}:{interval}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)

        if df is None or df.empty:
            logger.warning("No OHLCV data for %s (period=%s, interval=%s)", ticker, period, interval)
            return None

        # Keep only the standard OHLCV columns
        ohlcv_cols = ["Open", "High", "Low", "Close", "Volume"]
        available_cols = [c for c in ohlcv_cols if c in df.columns]
        df = df[available_cols].copy()

        # Drop rows where all OHLCV values are NaN, then forward-fill sparse gaps
        df.dropna(how="all", inplace=True)
        df.sort_index(ascending=True, inplace=True)

        if df.empty:
            logger.warning("OHLCV data empty after cleaning for %s", ticker)
            return None

        market = detect_market(ticker)
        currency = "MXN" if market == "MX" else "USD"

        result = OHLCVData(
            ticker=ticker,
            df=df,
            currency=currency,
            interval=interval,
        )

        _set_cache(cache_key, result, CACHE_TTL_OHLCV)
        return result

    except Exception as e:
        logger.warning("Failed to fetch OHLCV for %s: %s", ticker, e)
        return None


def get_multiple_quotes(tickers: list) -> Dict[str, Optional[StockInfo]]:
    """Fetch snapshot for multiple tickers. Returns dict of ticker -> StockInfo."""
    results: Dict[str, Optional[StockInfo]] = {}
    for ticker in tickers:
        results[ticker] = get_stock_info(ticker)
    return results
