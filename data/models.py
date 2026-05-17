"""StockWatch data models — contracts between data, analysis, and UI layers."""

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class SearchResult:
    ticker: str
    name: str
    market: str        # 'US' or 'MX'
    asset_type: str    # 'Acción' or 'ETF'
    exchange: str


@dataclass
class OHLCVData:
    ticker: str
    df: pd.DataFrame  # columns: Open, High, Low, Close, Volume; index=datetime
    currency: str
    interval: str


@dataclass
class StockInfo:
    ticker: str
    name: str
    market: str
    currency: str
    price: float
    change: float
    change_pct: float
    volume: int
    avg_volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    eps: Optional[float]
    dividend_yield: Optional[float]
    dividend_rate: Optional[float]
    week_52_high: float
    week_52_low: float
    beta: Optional[float]
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    expense_ratio: Optional[float] = None
    category: Optional[str] = None
    asset_type: str = "Acción"  # 'Acción' or 'ETF'


@dataclass
class IndicatorData:
    ticker: str
    rsi: pd.Series
    macd: pd.Series
    macd_signal_line: pd.Series
    macd_hist: pd.Series
    bb_upper: pd.Series
    bb_lower: pd.Series
    bb_mid: pd.Series
    ema_short: pd.Series
    ema_long: pd.Series
    sma_200: pd.Series


@dataclass
class SignalResult:
    ticker: str
    signal: str        # 'COMPRA' / 'VENTA' / 'NEUTRAL'
    confidence: str    # 'Alta' / 'Media' / 'Baja'
    score: int         # -10 to +10
    reasons: list = field(default_factory=list)
    rsi_value: float = 0.0
    rsi_signal: str = 'Neutral'
    macd_signal: str = 'Neutral'
    bb_signal: str = 'Dentro de bandas'
    trend_signal: str = 'Sin tendencia clara'
