"""
StockWatch Signal Engine
------------------------
Composite buy/sell/hold signal from multiple technical indicators.

Scoring system (conservative thresholds for investment decisions):
  RSI:
    < 30 (oversold):    +2 COMPRA
    30-40:              +1 COMPRA
    > 70 (overbought):  -2 VENTA
    60-70:              -1 VENTA
    else:                0 NEUTRAL

  MACD:
    Crossover UP (hist>0 and prev hist<=0): +2 COMPRA
    MACD > signal and hist > 0:             +1 COMPRA
    Crossover DOWN (hist<0 and prev hist>=0):-2 VENTA
    MACD < signal and hist < 0:             -1 VENTA
    else:                                    0 NEUTRAL

  Bollinger Bands:
    Price < lower band:                     +2 COMPRA
    Price in lower 20% of bands:            +1 COMPRA
    Price > upper band:                     -2 VENTA
    Price in upper 20% of bands:            -1 VENTA
    else:                                    0 NEUTRAL

  Trend (EMA20 vs EMA50 vs SMA200):
    EMA20 > EMA50 > SMA200:                +2 COMPRA
    EMA20 > EMA50:                          +1 COMPRA
    EMA20 < EMA50 < SMA200:               -2 VENTA
    EMA20 < EMA50:                         -1 VENTA
    else:                                    0 NEUTRAL

Final signal:
  score >= 3:  COMPRA  (confidence: Alta if |score|>=5, Media if >=3, Baja otherwise)
  score <= -3: VENTA
  else:        NEUTRAL
"""

import math
import logging
from typing import Optional, Tuple

import pandas as pd

from data.models import OHLCVData, SignalResult, IndicatorData
from analysis.indicators import compute_indicators

logger = logging.getLogger(__name__)


def generate_signal(ohlcv: OHLCVData) -> Optional[SignalResult]:
    """
    Generate composite buy/sell/hold signal.
    Returns None if indicators cannot be computed.
    """
    indicators = compute_indicators(ohlcv)
    if indicators is None:
        return None

    close = ohlcv.df["Close"]
    current_price = close.iloc[-1]

    # Get latest non-NaN values for point-in-time indicators
    rsi_val = _last_valid(indicators.rsi)
    bb_upper_val = _last_valid(indicators.bb_upper)
    bb_lower_val = _last_valid(indicators.bb_lower)
    bb_mid_val = _last_valid(indicators.bb_mid)
    ema_short_val = _last_valid(indicators.ema_short)
    ema_long_val = _last_valid(indicators.ema_long)
    sma_200_val = _last_valid(indicators.sma_200)

    # Score each component
    rsi_sc, rsi_label, rsi_reason = _rsi_score(rsi_val)
    macd_sc, macd_label, macd_reason = _macd_score(indicators.macd_hist)
    bb_sc, bb_label, bb_reason = _bb_score(
        current_price, bb_upper_val, bb_lower_val, bb_mid_val
    )
    trend_sc, trend_label, trend_reason = _trend_score(
        ema_short_val, ema_long_val, sma_200_val
    )

    # Aggregate
    total_score = rsi_sc + macd_sc + bb_sc + trend_sc
    total_score = max(-10, min(10, total_score))

    reasons = []
    for reason in [rsi_reason, macd_reason, bb_reason, trend_reason]:
        if reason:
            reasons.append(reason)

    # Determine signal and confidence
    abs_score = abs(total_score)
    if total_score >= 3:
        signal = "COMPRA"
    elif total_score <= -3:
        signal = "VENTA"
    else:
        signal = "NEUTRAL"

    if abs_score >= 5:
        confidence = "Alta"
    elif abs_score >= 3:
        confidence = "Media"
    else:
        confidence = "Baja"

    return SignalResult(
        ticker=ohlcv.ticker,
        signal=signal,
        confidence=confidence,
        score=total_score,
        reasons=reasons,
        rsi_value=rsi_val if not math.isnan(rsi_val) else 0.0,
        rsi_signal=rsi_label,
        macd_signal=macd_label,
        bb_signal=bb_label,
        trend_signal=trend_label,
    )


def _last_valid(series: pd.Series) -> float:
    """Return the last non-NaN value in a Series, or NaN if all NaN."""
    valid = series.dropna()
    if valid.empty:
        return float("nan")
    return float(valid.iloc[-1])


def _rsi_score(rsi_val: float) -> Tuple[int, str, str]:
    """Returns (score, signal_label, reason)."""
    if math.isnan(rsi_val):
        return 0, "Neutral", ""

    if rsi_val < 30:
        return 2, "Sobrevendido", f"RSI en zona de sobreventa (RSI={rsi_val:.1f})"
    elif rsi_val < 40:
        return 1, "Sobrevendido", f"RSI en zona de atención alcista (RSI={rsi_val:.1f})"
    elif rsi_val > 70:
        return -2, "Sobrecomprado", f"RSI en zona de sobrecompra (RSI={rsi_val:.1f})"
    elif rsi_val > 60:
        return -1, "Sobrecomprado", f"RSI mostrando señal de precaución (RSI={rsi_val:.1f})"
    else:
        return 0, "Neutral", ""


def _macd_score(macd_hist: pd.Series) -> Tuple[int, str, str]:
    """Returns (score, signal_label, reason). Uses last 2 values for crossover detection."""
    valid = macd_hist.dropna()
    if len(valid) < 2:
        return 0, "Neutral", ""

    curr = float(valid.iloc[-1])
    prev = float(valid.iloc[-2])

    # Crossover UP: hist turns positive
    if curr > 0 and prev <= 0:
        return 2, "Alcista", "Cruce alcista del MACD"
    # Crossover DOWN: hist turns negative
    if curr < 0 and prev >= 0:
        return -2, "Bajista", "Cruce bajista del MACD"
    # Sustained bullish momentum
    if curr > 0:
        return 1, "Alcista", "MACD con momentum alcista"
    # Sustained bearish momentum
    if curr < 0:
        return -1, "Bajista", "MACD con momentum bajista"

    return 0, "Neutral", ""


def _bb_score(
    price: float, bb_upper: float, bb_lower: float, bb_mid: float
) -> Tuple[int, str, str]:
    """Returns (score, signal_label, reason)."""
    if any(math.isnan(v) for v in [price, bb_upper, bb_lower, bb_mid]):
        return 0, "Dentro de bandas", ""

    band_width = bb_upper - bb_lower
    if band_width <= 0:
        return 0, "Dentro de bandas", ""

    if price < bb_lower:
        return 2, "Cerca del límite inferior", "Precio por debajo de banda inferior"

    if price > bb_upper:
        return -2, "Cerca del límite superior", "Precio por encima de banda superior"

    # Position within bands: 0 = at lower, 1 = at upper
    position = (price - bb_lower) / band_width

    if position <= 0.20:
        return 1, "Cerca del límite inferior", "Precio cerca de banda inferior"
    if position >= 0.80:
        return -1, "Cerca del límite superior", "Precio cerca de banda superior"

    return 0, "Dentro de bandas", ""


def _trend_score(
    ema_short: float, ema_long: float, sma_200: float
) -> Tuple[int, str, str]:
    """Returns (score, signal_label, reason)."""
    if any(math.isnan(v) for v in [ema_short, ema_long]):
        return 0, "Sin tendencia clara", ""

    sma_valid = not math.isnan(sma_200)

    # Strong bullish: EMA20 > EMA50 > SMA200
    if ema_short > ema_long and sma_valid and ema_long > sma_200:
        return (
            2,
            "Tendencia alcista",
            "Tendencia alcista confirmada (EMA20>EMA50>SMA200)",
        )

    # Strong bearish: EMA20 < EMA50 < SMA200
    if ema_short < ema_long and sma_valid and ema_long < sma_200:
        return (
            -2,
            "Tendencia bajista",
            "Tendencia bajista confirmada (EMA20<EMA50<SMA200)",
        )

    # Mild bullish
    if ema_short > ema_long:
        return 1, "Tendencia alcista", "EMA corta por encima de EMA larga"

    # Mild bearish
    if ema_short < ema_long:
        return -1, "Tendencia bajista", "EMA corta por debajo de EMA larga"

    return 0, "Sin tendencia clara", ""
