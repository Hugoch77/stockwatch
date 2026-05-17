# ─── StockWatch Configuration ─────────────────────────────────────────────────
# All constants in one place. No magic numbers elsewhere.

from dataclasses import dataclass, field
from typing import Optional, List
import pandas as pd

# ── App ──────────────────────────────────────────────────────────────────────
APP_NAME = "StockWatch"
APP_VERSION = "1.0.0"

# ── Markets ──────────────────────────────────────────────────────────────────
MARKETS = {
    "US": {
        "name": "Estados Unidos (NYSE/NASDAQ)",
        "suffix": "",
        "currency": "USD",
        "currency_symbol": "$",
        "exchange": "NYSE / NASDAQ",
    },
    "MX": {
        "name": "México (BMV)",
        "suffix": ".MX",
        "currency": "MXN",
        "currency_symbol": "$",
        "exchange": "BMV",
    },
}

# Popular Mexican stocks on BMV (for quick search suggestions)
MX_POPULAR_STOCKS = {
    "AMXL.MX": "América Móvil",
    "GFNORTEO.MX": "Grupo Financiero Banorte",
    "WALMEX*.MX": "Walmart de México",
    "FEMSAUBD.MX": "FEMSA",
    "CEMEXCPO.MX": "CEMEX",
    "BIMBOA.MX": "Grupo Bimbo",
    "ALSEA*.MX": "Alsea",
    "KOFUBL.MX": "Coca-Cola FEMSA",
    "LIVEPOLC-1.MX": "El Puerto de Liverpool",
    "GMEXICOB.MX": "Grupo México",
    "PINFRA*.MX": "Promotora y Operadora de Infraestructura",
    "GRUMAB.MX": "Gruma",
    "AC*.MX": "Arca Continental",
    "ALPEKA.MX": "Alpek",
    "ASURB.MX": "Grupo Aeroportuario del Sureste",
    "OMAB.MX": "Grupo Aeroportuario del Centro Norte",
    "GAPB.MX": "Grupo Aeroportuario del Pacífico",
    "FUNO11.MX": "Fibra Uno (REIT)",
    "SANMEXB.MX": "Banco Santander México",
    "CUERVO.MX": "José Cuervo",
}

# Popular US stocks/ETFs (quick suggestions)
US_POPULAR_STOCKS = {
    "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ (Nasdaq 100)",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet (Google)",
    "AMZN": "Amazon.com",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms",
    "TSLA": "Tesla Inc.",
    "BRK-B": "Berkshire Hathaway",
    "VTI": "Vanguard Total Stock Market ETF",
    "IVV": "iShares Core S&P 500 ETF",
    "VOO": "Vanguard S&P 500 ETF",
    "GLD": "SPDR Gold Shares",
    "VNQ": "Vanguard Real Estate ETF",
}

# ── Timeframes ────────────────────────────────────────────────────────────────
TIMEFRAMES = {
    "1S": {"label": "1 Semana", "period": "7d", "interval": "1h"},
    "1M": {"label": "1 Mes", "period": "1mo", "interval": "1d"},
    "3M": {"label": "3 Meses", "period": "3mo", "interval": "1d"},
    "6M": {"label": "6 Meses", "period": "6mo", "interval": "1d"},
    "1A": {"label": "1 Año", "period": "1y", "interval": "1d"},
    "3A": {"label": "3 Años", "period": "3y", "interval": "1wk"},
    "5A": {"label": "5 Años", "period": "5y", "interval": "1wk"},
    "MAX": {"label": "Máximo", "period": "max", "interval": "1mo"},
}
DEFAULT_TIMEFRAME = "1A"

# ── Cache TTLs (seconds) ──────────────────────────────────────────────────────
CACHE_TTL_QUOTE = 60          # Current price / snapshot
CACHE_TTL_OHLCV = 300         # Historical OHLCV
CACHE_TTL_FUNDAMENTALS = 3600  # Fundamental data (changes slowly)
CACHE_TTL_SEARCH = 1800        # Search results

# ── Technical Indicators ─────────────────────────────────────────────────────
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
EMA_SHORT = 20
EMA_LONG = 50
SMA_PERIODS = [20, 50, 200]
MIN_HISTORY_DAYS = 60  # Minimum days of data needed for indicators

# ── Signal Thresholds ─────────────────────────────────────────────────────────
SIGNAL_BULLISH_THRESHOLD = 3   # Minimum score for COMPRA signal
SIGNAL_BEARISH_THRESHOLD = -3  # Maximum score for VENTA signal
SIGNAL_CONFIDENCE_HIGH = 5     # Score |abs| for high confidence
SIGNAL_CONFIDENCE_MED = 3      # Score |abs| for medium confidence

# ── UI Colors ────────────────────────────────────────────────────────────────
COLOR_BULLISH = "#00C805"
COLOR_BEARISH = "#FF3131"
COLOR_NEUTRAL = "#888888"
COLOR_PRICE_LINE = "#2196F3"
COLOR_VOLUME = "#4CAF50"
COLOR_EMA_SHORT = "#FF9800"
COLOR_EMA_LONG = "#9C27B0"
COLOR_BB_UPPER = "rgba(173,216,230,0.3)"
COLOR_BB_LOWER = "rgba(173,216,230,0.3)"

# ── Dataclass Contracts ───────────────────────────────────────────────────────
# These are the interfaces between data/, analysis/, and ui/ layers.
# Hudson will implement these in data/models.py with full validation.


@dataclass
class SearchResult:
    ticker: str
    name: str
    market: str  # 'US' or 'MX'
    asset_type: str  # 'Acción' or 'ETF'
    exchange: str


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
    # ETF-specific (None for stocks)
    expense_ratio: Optional[float] = None
    category: Optional[str] = None


@dataclass
class OHLCVData:
    ticker: str
    df: object  # pd.DataFrame with Open, High, Low, Close, Volume index=datetime
    currency: str
    interval: str


@dataclass
class SignalResult:
    ticker: str
    signal: str       # 'COMPRA' / 'VENTA' / 'NEUTRAL'
    confidence: str   # 'Alta' / 'Media' / 'Baja'
    score: int        # -10 to +10
    reasons: List[str]
    rsi_value: float
    rsi_signal: str
    macd_signal: str
    bb_signal: str
    trend_signal: str  # based on EMA/SMA


@dataclass
class IndicatorData:
    ticker: str
    rsi: object       # pd.Series
    macd: object      # pd.Series
    macd_signal: object  # pd.Series
    macd_hist: object    # pd.Series
    bb_upper: object     # pd.Series
    bb_lower: object     # pd.Series
    bb_mid: object       # pd.Series
    ema_short: object    # pd.Series
    ema_long: object     # pd.Series
    sma_200: object      # pd.Series
