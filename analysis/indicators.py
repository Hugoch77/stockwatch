"""
StockWatch Technical Indicators
--------------------------------
All indicators use the `ta` (technical-analysis-library) package.
Input: OHLCVData with minimum MIN_HISTORY_DAYS of data.
Output: IndicatorData with all indicator Series aligned to the OHLCV index.

Formulas used:
- RSI(14): Relative Strength Index — Wilder's smoothing
- MACD(12,26,9): Moving Average Convergence Divergence
- Bollinger Bands(20, 2σ): Price envelope
- EMA(20): Exponential Moving Average short-term
- EMA(50): Exponential Moving Average long-term
- SMA(200): Simple Moving Average long-term trend
"""

import pandas as pd
import numpy as np
import ta
import logging
from typing import Optional

from data.models import OHLCVData, IndicatorData

logger = logging.getLogger(__name__)

RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
EMA_SHORT = 20
EMA_LONG = 50
SMA_LONG = 200
MIN_HISTORY_DAYS = 60

# Period mappings for performance stats (approximate trading days)
RETURN_PERIODS = {
    "return_1w": 5,
    "return_1m": 21,
    "return_3m": 63,
    "return_6m": 126,
    "return_1y": 252,
}


def compute_indicators(ohlcv: OHLCVData) -> Optional[IndicatorData]:
    """
    Compute all technical indicators from OHLCV data.
    Returns None if insufficient data (< MIN_HISTORY_DAYS rows).
    Uses ta library's momentum, trend, and volatility modules.
    """
    df = ohlcv.df.copy()
    if len(df) < MIN_HISTORY_DAYS:
        logger.warning(
            f"{ohlcv.ticker}: insufficient data ({len(df)} rows < {MIN_HISTORY_DAYS})"
        )
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # RSI
    rsi = ta.momentum.RSIIndicator(close=close, window=RSI_PERIOD).rsi()

    # MACD
    macd_indicator = ta.trend.MACD(
        close=close,
        window_fast=MACD_FAST,
        window_slow=MACD_SLOW,
        window_sign=MACD_SIGNAL,
    )
    macd = macd_indicator.macd()
    macd_signal_line = macd_indicator.macd_signal()
    macd_hist = macd_indicator.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(
        close=close, window=BB_PERIOD, window_dev=BB_STD
    )
    bb_upper = bb.bollinger_hband()
    bb_lower = bb.bollinger_lband()
    bb_mid = bb.bollinger_mavg()

    # EMAs and SMA
    ema_short = ta.trend.EMAIndicator(close=close, window=EMA_SHORT).ema_indicator()
    ema_long = ta.trend.EMAIndicator(close=close, window=EMA_LONG).ema_indicator()
    sma_200 = ta.trend.SMAIndicator(close=close, window=SMA_LONG).sma_indicator()

    return IndicatorData(
        ticker=ohlcv.ticker,
        rsi=rsi,
        macd=macd,
        macd_signal_line=macd_signal_line,
        macd_hist=macd_hist,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        bb_mid=bb_mid,
        ema_short=ema_short,
        ema_long=ema_long,
        sma_200=sma_200,
    )


def get_performance_stats(ohlcv: OHLCVData) -> dict:
    """
    Compute performance statistics:
    - Returns over 1W, 1M, 3M, 6M, 1Y periods (if data available)
    - Volatility (annualized standard deviation of daily returns)
    - Max drawdown
    - Average daily volume
    All as percentages where applicable.
    """
    df = ohlcv.df.copy()
    close = df["Close"]
    stats: dict = {}

    # Period returns: compare current close to close N trading days ago
    current_price = close.iloc[-1]
    for key, days in RETURN_PERIODS.items():
        if len(close) > days:
            past_price = close.iloc[-days - 1]
            stats[key] = ((current_price - past_price) / past_price) * 100.0
        else:
            stats[key] = None

    # Annualized volatility
    daily_returns = close.pct_change().dropna()
    if len(daily_returns) > 1:
        stats["volatility_annual"] = float(
            daily_returns.std() * np.sqrt(252) * 100.0
        )
    else:
        stats["volatility_annual"] = None

    # Max drawdown over the entire period
    cumulative_max = close.cummax()
    drawdown = (close - cumulative_max) / cumulative_max
    stats["max_drawdown"] = float(drawdown.min() * 100.0)

    # Average daily volume
    stats["avg_volume"] = int(df["Volume"].mean()) if "Volume" in df.columns else 0

    return stats
