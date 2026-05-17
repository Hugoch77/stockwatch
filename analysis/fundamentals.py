"""
StockWatch Fundamental Analysis
---------------------------------
Interprets fundamental data for investment decisions.
Formats valuation metrics with context (is P/E high/low for sector?).
Handles both stocks and ETFs differently.
"""

from typing import Optional

from data.models import StockInfo

# P/E benchmarks by sector (approximate market averages)
PE_BENCHMARKS = {
    "Technology": 30,
    "Healthcare": 25,
    "Financials": 15,
    "Energy": 12,
    "Consumer Defensive": 20,
    "Consumer Cyclical": 22,
    "Industrials": 20,
    "Real Estate": 35,
    "Communication Services": 25,
    "Materials": 18,
    "Utilities": 18,
    "default": 20,
}


def interpret_pe(pe_ratio: Optional[float], sector: Optional[str] = None) -> dict:
    """
    Returns P/E interpretation with sector-relative context.
    """
    if pe_ratio is None or pe_ratio <= 0:
        return {
            "value": None,
            "benchmark": None,
            "label": "N/D",
            "interpretation": "P/E no disponible o negativo (empresa sin ganancias).",
        }

    benchmark = PE_BENCHMARKS.get(sector, PE_BENCHMARKS["default"]) if sector else PE_BENCHMARKS["default"]
    ratio = pe_ratio / benchmark

    if ratio > 1.3:
        label = "Caro"
        interpretation = (
            f"P/E de {pe_ratio:.1f} está por encima del promedio del sector "
            f"({benchmark}). La acción podría estar sobrevaluada."
        )
    elif ratio < 0.7:
        label = "Barato"
        interpretation = (
            f"P/E de {pe_ratio:.1f} está por debajo del promedio del sector "
            f"({benchmark}). Podría representar una oportunidad de valor."
        )
    else:
        label = "Justo"
        interpretation = (
            f"P/E de {pe_ratio:.1f} está en línea con el promedio del sector ({benchmark})."
        )

    return {
        "value": pe_ratio,
        "benchmark": benchmark,
        "label": label,
        "interpretation": interpretation,
    }


def interpret_dividend(dividend_yield: Optional[float]) -> dict:
    """
    Returns dividend yield interpretation.
    Benchmarks: >4% high, 2-4% moderate, 0-2% low, 0/None none.
    """
    if dividend_yield is None or dividend_yield <= 0:
        return {
            "value": 0.0,
            "label": "Sin dividendo",
            "interpretation": "Esta acción no paga dividendos actualmente.",
        }

    pct = dividend_yield * 100.0 if dividend_yield < 1 else dividend_yield

    if pct > 4.0:
        label = "Alto"
        interpretation = (
            f"Rendimiento por dividendo de {pct:.2f}% — alto, atractivo para ingreso pasivo."
        )
    elif pct >= 2.0:
        label = "Moderado"
        interpretation = (
            f"Rendimiento por dividendo de {pct:.2f}% — moderado, buen complemento."
        )
    else:
        label = "Bajo"
        interpretation = (
            f"Rendimiento por dividendo de {pct:.2f}% — bajo, la empresa prioriza reinversión."
        )

    return {
        "value": pct,
        "label": label,
        "interpretation": interpretation,
    }


def interpret_52w_position(
    price: float, week_52_high: float, week_52_low: float
) -> dict:
    """
    Returns 52-week range position analysis.
    """
    range_size = week_52_high - week_52_low
    if range_size <= 0:
        return {
            "pct_from_low": 0.0,
            "pct_from_high": 0.0,
            "position": 50.0,
            "label": "Zona media",
        }

    pct_from_low = ((price - week_52_low) / week_52_low) * 100.0 if week_52_low > 0 else 0.0
    pct_from_high = ((week_52_high - price) / week_52_high) * 100.0 if week_52_high > 0 else 0.0
    position = ((price - week_52_low) / range_size) * 100.0

    if position >= 80:
        label = "Cerca del máximo"
    elif position <= 20:
        label = "Cerca del mínimo"
    else:
        label = "Zona media"

    return {
        "pct_from_low": round(pct_from_low, 2),
        "pct_from_high": round(pct_from_high, 2),
        "position": round(position, 2),
        "label": label,
    }


def interpret_beta(beta: Optional[float]) -> dict:
    """
    Returns beta/risk interpretation.
    Benchmarks: >1.5 high, 0.7-1.5 moderate, <0.7 low.
    """
    if beta is None:
        return {
            "value": None,
            "label": "N/D",
            "interpretation": "Beta no disponible.",
        }

    if beta > 1.5:
        label = "Alta volatilidad"
        interpretation = (
            f"Beta de {beta:.2f} — se mueve significativamente más que el mercado. Mayor riesgo."
        )
    elif beta >= 0.7:
        label = "Volatilidad moderada"
        interpretation = (
            f"Beta de {beta:.2f} — se mueve de forma similar al mercado."
        )
    else:
        label = "Baja volatilidad"
        interpretation = (
            f"Beta de {beta:.2f} — menos volátil que el mercado. Opción defensiva."
        )

    return {
        "value": beta,
        "label": label,
        "interpretation": interpretation,
    }


def _market_cap_label(market_cap: Optional[float]) -> str:
    """Classify market cap in USD."""
    if market_cap is None:
        return "N/D"
    if market_cap >= 200_000_000_000:
        return "Mega Cap"
    if market_cap >= 10_000_000_000:
        return "Large Cap"
    if market_cap >= 2_000_000_000:
        return "Mid Cap"
    return "Small Cap"


def _expense_ratio_info(expense_ratio: Optional[float]) -> dict:
    """Classify ETF expense ratio."""
    if expense_ratio is None:
        return {"value": None, "label": "N/D"}
    pct = expense_ratio * 100.0 if expense_ratio < 1 else expense_ratio
    if pct < 0.10:
        label = "Muy bajo"
    elif pct <= 0.50:
        label = "Bajo"
    elif pct <= 1.0:
        label = "Moderado"
    else:
        label = "Alto"
    return {"value": round(pct, 3), "label": label}


def get_fundamental_summary(info: StockInfo) -> dict:
    """
    Returns a complete fundamental analysis dict combining all interpretations.
    Handles ETFs separately from stocks.
    """
    is_etf = info.expense_ratio is not None or info.category is not None

    position_52w = interpret_52w_position(info.price, info.week_52_high, info.week_52_low)
    dividend = interpret_dividend(info.dividend_yield)
    risk = interpret_beta(info.beta)
    cap_label = _market_cap_label(info.market_cap)

    result: dict = {
        "asset_type": "ETF" if is_etf else "Acción",
        "dividend": dividend,
        "position_52w": position_52w,
        "risk": risk,
        "market_cap_label": cap_label,
        "overall_notes": [],
    }

    if is_etf:
        result["expense_ratio"] = _expense_ratio_info(info.expense_ratio)
        # No P/E for ETFs
    else:
        result["valuation"] = interpret_pe(info.pe_ratio, info.sector)

    # Generate overall investment notes in Spanish
    notes = []

    if not is_etf:
        pe_info = result.get("valuation", {})
        if pe_info.get("label") == "Barato":
            notes.append(
                "Valuación atractiva: P/E por debajo del promedio del sector."
            )
        elif pe_info.get("label") == "Caro":
            notes.append(
                "Valuación elevada: P/E por encima del promedio del sector."
            )

    if dividend.get("label") == "Alto":
        notes.append(
            f"Dividendo alto ({dividend['value']:.2f}%) — buena opción para ingreso pasivo."
        )

    if position_52w.get("label") == "Cerca del mínimo":
        notes.append(
            "Precio cerca del mínimo de 52 semanas — posible oportunidad si los fundamentales son sólidos."
        )
    elif position_52w.get("label") == "Cerca del máximo":
        notes.append(
            "Precio cerca del máximo de 52 semanas — considerar si queda potencial alcista."
        )

    if risk.get("label") == "Alta volatilidad":
        notes.append("Beta alto — activo más volátil que el mercado, mayor riesgo.")

    if is_etf:
        er = result.get("expense_ratio", {})
        if er.get("label") in ("Muy bajo", "Bajo"):
            notes.append(
                f"Gasto operativo eficiente ({er.get('value', 0):.2f}%)."
            )
        elif er.get("label") == "Alto":
            notes.append(
                f"Gasto operativo elevado ({er.get('value', 0):.2f}%) — comparar con alternativas."
            )

    # Ensure at least 2 notes
    if len(notes) == 0:
        notes.append("Perfil fundamentales dentro de rangos normales.")
        notes.append("Revisar tendencias técnicas para complementar el análisis.")
    elif len(notes) == 1:
        notes.append("Revisar tendencias técnicas para complementar el análisis.")

    result["overall_notes"] = notes[:3]

    return result
