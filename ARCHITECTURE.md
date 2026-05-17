# StockWatch — Arquitectura del Sistema

## 1. Visión General

StockWatch es una aplicación local construida con Python y Streamlit para análisis de acciones y ETFs de mercados de **México (BMV)** y **Estados Unidos (NYSE/NASDAQ)**. Está diseñada para inversores que operan con brokers como **GBM**, que ofrecen acceso a ambos mercados.

### Principios de Diseño

- **100% local:** No requiere servidor, corre en la máquina del usuario
- **Datos gratuitos:** Yahoo Finance vía `yfinance` — sin API key, sin costos
- **Bilingüe de mercado:** Soporta tickers US (AAPL) y MX con sufijo `.MX` (AMXL.MX)
- **Señales informativas:** Indicadores técnicos como herramienta de análisis, no asesoría financiera
- **Separación clara:** Tres capas independientes (data → analysis → ui)

## 2. Estructura del Proyecto

```
stockwatch/
├── app.py                    # Entry point — Streamlit + navegación
├── config.py                 # Constantes, mercados, parámetros, dataclasses
├── requirements.txt          # Dependencias Python
├── README.md                 # Guía de instalación y uso
├── ARCHITECTURE.md           # Este documento
│
├── data/                     # Capa de datos (Owner: Hudson)
│   ├── __init__.py
│   ├── models.py             # Dataclasses: StockInfo, OHLCVData, etc.
│   ├── fetcher.py            # Wrapper de yfinance + caché
│   └── search.py             # Búsqueda de tickers por nombre
│
├── analysis/                 # Capa de análisis (Owner: Vasquez)
│   ├── __init__.py
│   ├── indicators.py         # RSI, MACD, Bollinger Bands, EMA/SMA
│   ├── signals.py            # Señales compuestas (COMPRA/VENTA/NEUTRAL)
│   └── fundamentals.py       # Formateo de datos fundamentales
│
└── ui/                       # Capa de presentación (Owner: Bishop)
    ├── __init__.py
    ├── search_page.py        # Página principal con buscador
    ├── detail_page.py        # Análisis completo de un activo
    ├── comparison_page.py    # Comparación de múltiples activos
    └── components.py         # Componentes reutilizables
```

## 3. Capas de la Arquitectura

### 3.1 Capa de Datos (`data/`)

**Responsabilidad:** Obtener y cachear datos de Yahoo Finance.

**Fuente de datos:** `yfinance` (Yahoo Finance Python library)
- No requiere API key
- Soporta mercados globales vía sufijos de ticker
- US stocks: tickers estándar (`AAPL`, `MSFT`, `SPY`)
- Mexican stocks (BMV): sufijo `.MX` (`AMXL.MX`, `GFNORTEO.MX`, `CEMEXCPO.MX`)
- Búsqueda: `yfinance.Search(query)` para encontrar tickers por nombre de empresa

**Módulos:**

| Archivo | Función |
|---------|---------|
| `models.py` | Dataclasses que definen contratos entre capas |
| `fetcher.py` | Wrapper de `yfinance.Ticker()` y `.history()` con caché en memoria |
| `search.py` | Búsqueda de tickers usando `yfinance.Search()` + sugerencias populares |

**Caché en memoria (Streamlit `@st.cache_data`):**

| Dato | TTL | Razón |
|------|-----|-------|
| Cotización actual | 60s | Precio cambia constantemente |
| Datos OHLCV | 300s | Histórico cambia solo al cierre |
| Datos fundamentales | 3600s | Cambian trimestralmente |
| Resultados de búsqueda | 1800s | Relativamente estáticos |

### 3.2 Capa de Análisis (`analysis/`)

**Responsabilidad:** Calcular indicadores técnicos y generar señales de inversión.

**Indicadores técnicos:**

| Indicador | Parámetros | Uso |
|-----------|-----------|-----|
| RSI | Periodo: 14, Oversold: 30, Overbought: 70 | Momentum / sobrecompra-sobreventa |
| MACD | Fast: 12, Slow: 26, Signal: 9 | Tendencia + momentum |
| Bollinger Bands | Periodo: 20, Desviación: 2σ | Volatilidad + reversal zones |
| EMA | Corto: 20, Largo: 50 | Tendencia corto/largo plazo |
| SMA | Periodos: 20, 50, 200 | Tendencia + soportes/resistencias |

**Sistema de señales:**
- Cada indicador aporta puntos (+/−) al score compuesto
- Score ≥ +3 → **COMPRA** | Score ≤ −3 → **VENTA** | Intermedio → **NEUTRAL**
- Confianza: Alta (|score| ≥ 5), Media (|score| ≥ 3), Baja (resto)
- Cada señal incluye lista de razones en español para transparencia

**Datos fundamentales:**
- P/E ratio, EPS, dividend yield, beta, market cap
- Sector e industria
- Datos específicos de ETFs (expense ratio, categoría)
- Formateados para visualización directa

### 3.3 Capa de UI (`ui/`)

**Responsabilidad:** Presentar datos y análisis al usuario con gráficos interactivos Plotly.

**Páginas:**

| Página | Ruta | Función |
|--------|------|---------|
| Búsqueda | `search_page.py` | Landing page — buscar por ticker o nombre, sugerencias populares MX y US |
| Análisis | `detail_page.py` | Vista completa de un activo — precio, indicadores, señales, fundamentales |
| Comparar | `comparison_page.py` | Comparar múltiples activos lado a lado |

**Navegación:**
- Estado de página en `st.session_state.page`
- Ticker seleccionado en `st.session_state.selected_ticker`
- Lista de comparación en `st.session_state.compare_tickers`
- Sidebar con botones de navegación y info del broker (GBM)

## 4. Flujo de Datos

```
Usuario busca "América Móvil"
    │
    ▼
search.py → yfinance.Search("América Móvil") → [SearchResult(AMXL.MX, ...)]
    │
    ▼
Usuario selecciona AMXL.MX
    │
    ▼
fetcher.py → yfinance.Ticker("AMXL.MX") → StockInfo + OHLCVData
    │
    ▼
indicators.py → RSI, MACD, BB, EMA, SMA → IndicatorData
    │
    ▼
signals.py → score compuesto → SignalResult(COMPRA/VENTA/NEUTRAL)
    │
    ▼
detail_page.py → gráficos Plotly + métricas + señal
```

## 5. Mercados y Tickers

### Convención de Tickers Yahoo Finance

| Mercado | Formato | Ejemplos |
|---------|---------|----------|
| NYSE / NASDAQ | Ticker directo | `AAPL`, `MSFT`, `SPY` |
| BMV (México) | Ticker + `.MX` | `AMXL.MX`, `CEMEXCPO.MX` |

### Detección de mercado
- Tickers que terminan en `.MX` → mercado mexicano (BMV), moneda MXN
- Todos los demás → mercado US (NYSE/NASDAQ), moneda USD

### Relevancia para GBM
GBM (Grupo Bursátil Mexicano) ofrece acceso a:
- **BMV:** Acciones mexicanas directamente
- **SIC (Sistema Internacional de Cotizaciones):** Acciones y ETFs de US listados en BMV

Esta app cubre ambos mercados que un inversor de GBM puede operar.

## 6. Contratos entre Capas (Dataclasses)

Definidas en `config.py` como referencia, implementadas en `data/models.py`:

| Dataclass | Propósito | Campos clave |
|-----------|-----------|--------------|
| `SearchResult` | Resultado de búsqueda | ticker, name, market, asset_type |
| `StockInfo` | Snapshot de un activo | price, change, PE, dividend, sector |
| `OHLCVData` | Datos históricos | DataFrame OHLCV, ticker, currency |
| `SignalResult` | Señal de inversión | signal, confidence, score, reasons |
| `IndicatorData` | Indicadores calculados | RSI, MACD, BB, EMA, SMA series |

## 7. Dependencias

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `streamlit` | ≥1.32.0 | Framework de UI |
| `yfinance` | ≥0.2.38 | Datos de Yahoo Finance |
| `pandas` | ≥2.0.0 | Manipulación de datos |
| `numpy` | ≥1.24.0 | Cálculos numéricos |
| `plotly` | ≥5.18.0 | Gráficos interactivos |
| `ta` | ≥0.11.0 | Indicadores técnicos |
| `requests` | ≥2.31.0 | HTTP (dependencia de yfinance) |

## 8. Comparación con CryptoWatch

StockWatch hereda la arquitectura probada de CryptoWatch con adaptaciones:

| Aspecto | CryptoWatch | StockWatch |
|---------|-------------|------------|
| **Mercados** | Cripto (CoinGecko/Binance) | Acciones + ETFs (Yahoo Finance) |
| **Data source** | APIs REST con rate limiting | `yfinance` library (sin rate limit estricto) |
| **Caché** | Custom dict con TTL + Lock | Streamlit `@st.cache_data` con TTL |
| **Tickers** | ID de CoinGecko (bitcoin) | Yahoo Finance (AAPL, AMXL.MX) |
| **Señales** | Mismo motor de scoring | Mismo motor, adaptado a acciones |
| **Indicadores** | RSI, MACD, BB, EMA, SMA | Idénticos + datos fundamentales |
| **UI** | Overview, Detail, Comparison | Search, Detail, Comparison |

## 9. Decisiones Arquitectónicas

1. **yfinance sobre APIs REST directas:** Abstrae la complejidad de Yahoo Finance, maneja rate limiting internamente, soporte nativo para mercados globales.

2. **Sufijo `.MX` para BMV:** Convención estándar de Yahoo Finance. Permite usar la misma API para ambos mercados sin cambios.

3. **Streamlit cache sobre cache custom:** `@st.cache_data` es más simple y se integra nativamente con el ciclo de re-render de Streamlit.

4. **`ta` library sobre cálculos manuales:** Biblioteca probada y mantenida para indicadores técnicos. Reduce bugs en cálculos matemáticos.

5. **Tres capas (data/analysis/ui):** Separación de responsabilidades clara. Cada capa tiene un owner distinto en el equipo.

6. **Timeframes en español:** Labels de usuario en español (1 Semana, 1 Mes, etc.) mapeados a intervalos de yfinance.

## 10. Limitaciones Conocidas

- **Datos en tiempo real:** yfinance tiene ~15 min de delay en datos intradía
- **BMV coverage:** Algunos tickers de BMV pueden no estar disponibles en Yahoo Finance
- **Sin autenticación GBM:** La app no se conecta directamente al broker — es solo análisis
- **Sin portafolio tracking:** v1 no incluye seguimiento de portafolio personal
