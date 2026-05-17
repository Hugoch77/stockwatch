"""
StockWatch Investment Simulator
---------------------------------
Compute historical return metrics from OHLCV data and project investment
outcomes at multiple time horizons. Pure pandas/numpy — no new dependencies.

All user-facing text is in Spanish. Outputs are for informational purposes
only; see get_simulation_disclaimer() for mandatory legal notice.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Human-readable Spanish labels for each horizon (years → label)
_HORIZON_LABELS = {
    1 / 12: "1 Mes",
    3 / 12: "3 Meses",
    6 / 12: "6 Meses",
    1.0: "1 Año",
    2.0: "2 Años",
    3.0: "3 Años",
    5.0: "5 Años",
    10.0: "10 Años",
}

DEFAULT_HORIZONS = [1 / 12, 3 / 12, 6 / 12, 1.0, 2.0, 3.0, 5.0, 10.0]


def calculate_historical_returns(df: pd.DataFrame) -> dict:
    """
    Derive historical return statistics from a Close-price series.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV frame with at least a 'Close' column and a datetime index.

    Returns
    -------
    dict with keys:
        cagr               – Compound Annual Growth Rate (decimal, e.g. 0.12 = 12 %)
        avg_monthly_return – Mean monthly % return (decimal)
        volatility         – Annualised daily-return std (decimal)
        best_year          – Highest calendar-year return (decimal)
        worst_year         – Lowest  calendar-year return (decimal)
        max_drawdown       – Maximum peak-to-trough decline (decimal, negative)
        data_years         – Approximate years of data used
    """
    result = {
        "cagr": 0.0,
        "avg_monthly_return": 0.0,
        "volatility": 0.0,
        "best_year": 0.0,
        "worst_year": 0.0,
        "max_drawdown": 0.0,
        "data_years": 0.0,
    }

    if df is None or df.empty or "Close" not in df.columns:
        return result

    close = df["Close"].dropna()
    if len(close) < 2:
        return result

    # ── Data coverage ──────────────────────────────────────────────────────
    try:
        first_date = close.index[0]
        last_date = close.index[-1]
        data_years = (last_date - first_date).days / 365.25
    except Exception:
        data_years = len(close) / 252.0
    result["data_years"] = round(data_years, 2)

    first_price = float(close.iloc[0])
    last_price = float(close.iloc[-1])

    if first_price <= 0 or data_years <= 0:
        return result

    # ── CAGR ───────────────────────────────────────────────────────────────
    try:
        cagr = (last_price / first_price) ** (1.0 / data_years) - 1.0
        result["cagr"] = float(np.clip(cagr, -0.99, 10.0))
    except Exception:
        result["cagr"] = 0.0

    # ── Daily returns ──────────────────────────────────────────────────────
    daily_returns = close.pct_change().dropna()

    # ── Annualised volatility ──────────────────────────────────────────────
    if len(daily_returns) > 1:
        result["volatility"] = float(daily_returns.std() * np.sqrt(252))

    # ── Average monthly return ─────────────────────────────────────────────
    try:
        monthly_close = close.resample("ME").last().dropna()
        if len(monthly_close) >= 2:
            monthly_returns = monthly_close.pct_change().dropna()
            result["avg_monthly_return"] = float(monthly_returns.mean())
    except Exception:
        result["avg_monthly_return"] = float(
            ((1 + result["cagr"]) ** (1 / 12) - 1)
        )

    # ── Yearly returns ─────────────────────────────────────────────────────
    try:
        yearly_close = close.resample("YE").last().dropna()
        if len(yearly_close) >= 2:
            yearly_returns = yearly_close.pct_change().dropna()
            result["best_year"] = float(yearly_returns.max())
            result["worst_year"] = float(yearly_returns.min())
        else:
            # Fewer than 2 complete years — approximate from CAGR ± volatility
            vol = result["volatility"]
            cagr_val = result["cagr"]
            result["best_year"] = float(cagr_val + vol)
            result["worst_year"] = float(cagr_val - vol)
    except Exception:
        vol = result["volatility"]
        cagr_val = result["cagr"]
        result["best_year"] = float(cagr_val + vol)
        result["worst_year"] = float(cagr_val - vol)

    # Clamp yearly returns to sane range
    result["best_year"] = float(np.clip(result["best_year"], -0.99, 50.0))
    result["worst_year"] = float(np.clip(result["worst_year"], -0.99, 50.0))

    # ── Max drawdown ───────────────────────────────────────────────────────
    try:
        cummax = close.cummax()
        drawdown = (close - cummax) / cummax
        result["max_drawdown"] = float(drawdown.min())
    except Exception:
        result["max_drawdown"] = 0.0

    return result


def simulate_investment(
    amount: float,
    historical_returns: dict,
    horizons: Optional[list] = None,
) -> list:
    """
    Project an investment across multiple time horizons using historical stats.

    Parameters
    ----------
    amount             : float — Amount invested (in the asset's native currency)
    historical_returns : dict  — Output of calculate_historical_returns()
    horizons           : list  — Years per horizon; defaults to DEFAULT_HORIZONS

    Returns
    -------
    List of dicts, one per horizon, each with:
        years             – Numeric years
        label             – Spanish label (e.g. "1 Año")
        projected_value   – CAGR-based projected value (compound)
        simple_value      – Simple-interest projection: amount * (1 + cagr * years)
        compound_advantage– Extra gain from compounding: projected_value - simple_value
        optimistic_value  – Best-year-based projection
        pessimistic_value – Worst-year-based projection (clamped at 1 % of amount)
        gain_loss         – projected_value − amount
        gain_loss_pct     – % gain/loss vs initial amount
        low_data_warning  – True if data_years < 3 (scenarios less reliable)
    """
    if horizons is None:
        horizons = DEFAULT_HORIZONS

    data_years = historical_returns.get("data_years", 0.0)

    if data_years < 1.0:
        logger.warning("simulate_investment: insufficient data (< 1 year). Returning empty list.")
        return []

    cagr = historical_returns.get("cagr", 0.0)
    best_year = historical_returns.get("best_year", cagr)
    worst_year = historical_returns.get("worst_year", cagr)
    low_data_warning = data_years < 3.0

    results = []
    for years in horizons:
        label = _HORIZON_LABELS.get(years, f"{years:.1f} Años")

        # Projected (base case: CAGR — compound growth)
        projected_value = amount * ((1.0 + cagr) ** years)

        # Simple interest baseline: same CAGR applied linearly (no reinvestment)
        simple_value = amount * (1.0 + cagr * years)

        # Extra money earned purely because of compounding
        compound_advantage = projected_value - simple_value

        # Optimistic: best calendar year annualised
        optimistic_value = amount * ((1.0 + best_year) ** years)

        # Pessimistic: worst calendar year annualised, never below 1 % of principal
        raw_pessimistic = amount * ((1.0 + worst_year) ** years)
        pessimistic_value = max(raw_pessimistic, amount * 0.01)

        gain_loss = projected_value - amount
        gain_loss_pct = (projected_value / amount - 1.0) * 100.0 if amount != 0 else 0.0

        results.append(
            {
                "years": years,
                "label": label,
                "projected_value": round(projected_value, 2),
                "simple_value": round(simple_value, 2),
                "compound_advantage": round(compound_advantage, 2),
                "optimistic_value": round(optimistic_value, 2),
                "pessimistic_value": round(pessimistic_value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_pct": round(gain_loss_pct, 2),
                "low_data_warning": low_data_warning,
            }
        )

    return results


def get_simulation_disclaimer() -> str:
    """Return a mandatory Spanish disclaimer for the simulator."""
    return (
        "⚠️ Las proyecciones se basan en rendimientos históricos. "
        "El rendimiento pasado no garantiza resultados futuros. "
        "Esto no es asesoría de inversión."
    )
