# 📈 StockWatch — Análisis de Inversión v1.0.0

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0%2B-FF4B4B)](https://streamlit.io/)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**StockWatch** es una aplicación local, de código abierto, para análisis técnico y fundamental de acciones y ETFs en mercados de México (BMV) y Estados Unidos (NYSE/NASDAQ). Diseñada para inversores independientes que operan con brokers como GBM y requieren herramientas de análisis ágiles, sin dependencias de servidores externo.

---

## 📋 Tabla de contenidos

- [Descripción](#descripción)
- [Funcionalidades](#funcionalidades)
- [Mercados soportados](#mercados-soportados)
- [Indicadores técnicos](#indicadores-técnicos)
- [Sistema de señales](#sistema-de-señales)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Configuración](#configuración)
- [Stack tecnológico](#stack-tecnológico)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Aviso legal](#aviso-legal)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## 📖 Descripción

**StockWatch** es una herramienta de análisis de mercado 100% local, sin requerimientos de servidor backend. Proporciona acceso a datos gratuitos de Yahoo Finance, permitiendo análisis técnico profundo con indicadores avanzados, señales automatizadas y comparativas lado a lado.

La aplicación está construida con **Streamlit** para una interfaz web responsive y **Python** como base computacional, con separación clara en 3 capas arquitectónicas:

1. **Data Layer** — Obtención, cacheo y validación de datos (yfinance)
2. **Analysis Layer** — Cálculo de indicadores, señales y análisis fundamentales
3. **UI Layer** — Interfaz interactiva con 3 páginas principales

Ideal para inversores que necesitan:
- ✅ Análisis técnico rápido en tiempo local
- ✅ Señales informativas basadas en múltiples indicadores
- ✅ Acceso simultáneo a mercados mexicano y estadounidense
- ✅ Sin costos de suscripción (datos gratuitos)
- ✅ Privacidad total (ejecución local, sin datos en la nube)

---

## 💡 Funcionalidades

### 🔍 Búsqueda inteligente
- Buscador por ticker o nombre de empresa
- Sugerencias rápidas de acciones populares (MX y USA)
- Detección automática del mercado
- Filtro por tipo de activo (acción o ETF)

### 📊 Análisis detallado
- **Gráficos interactivos** con Plotly (zoom, pausa, hover)
- **Indicadores técnicos** en tiempo real (RSI, MACD, Bollinger Bands, EMAs, SMAs)
- **Datos fundamentales** (P/E, dividend yield, beta, market cap, etc.)
- **Señales automáticas** con scoring -10 a +10 y justificaciones en español
- **Múltiples timeframes**: 1 Semana, 1 Mes, 3 Meses, 6 Meses, 1 Año (defecto), 3 Años, 5 Años, Máximo

### ⚖️ Comparación
- Análisis lado a lado de múltiples activos
- Comparación de rendimiento histórico
- Evaluación visual de volatilidad y tendencias

### ⚡ Cacheo inteligente
- **Cotizaciones**: 60 segundos
- **Datos OHLCV**: 5 minutos
- **Fundamentales**: 1 hora
- **Resultados de búsqueda**: 30 minutos

---

## 🌍 Mercados soportados

| Mercado | Moneda | Exchange | Ejemplos |
|---------|--------|----------|----------|
| 🇺🇸 **USA** | USD | NYSE / NASDAQ | AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, SPY, QQQ, VOO, VTI, GLD |
| 🇲🇽 **México** | MXN | BMV | AMXL.MX, GFNORTEO.MX, WALMEX*.MX, FEMSAUBD.MX, CEMEXCPO.MX, BIMBOA.MX, KOFUBL.MX, ALSEA*.MX |

**Nota:** Todos los tickers mexicanos deben incluir el sufijo `.MX` para ser consultados correctamente en Yahoo Finance.

---

## 📈 Indicadores técnicos

| Indicador | Parámetros | Interpretación |
|-----------|-----------|-----------------|
| **RSI (Relative Strength Index)** | 14 periodos | ≤30: Sobreventa → COMPRA, ≥70: Sobrecompra → VENTA |
| **MACD** | Fast: 12, Slow: 26, Signal: 9 | Cruce de línea con signal → cambio de tendencia |
| **Bollinger Bands** | 20 periodos, ±2σ | Toque de banda → reversión esperada |
| **EMA (Exponential Moving Average)** | Corto: 20, Largo: 50 | Cruce de EMAs → cambio de tendencia |
| **SMA (Simple Moving Average)** | 20, 50, 200 periodos | Precio sobre/bajo SMA → tendencia alcista/bajista |

Todos los indicadores requieren un **mínimo de 60 días de histórico** para ser calculados.

---

## 🎯 Sistema de señales

StockWatch genera señales automáticas combinando todos los indicadores en un **scoring de -10 a +10**:

### Niveles de señal
- **COMPRA** 🟢: Score ≥ +3 (alcista, probabilidad de subida)
- **VENTA** 🔴: Score ≤ -3 (bajista, probabilidad de caída)
- **NEUTRAL** 🟡: Score entre -2 y +2 (indecisión o equilibrio)

### Niveles de confianza
- **Alta**: |score| ≥ 5 (múltiples indicadores alineados)
- **Media**: |score| ≥ 3 (mayoría de indicadores alineados)
- **Baja**: resto (divergencia o datos insuficientes)

### Razones de la señal
Cada señal incluye **justificaciones en español**:
- Posición respecto a bandas de Bollinger
- Estado de RSI (sobreventa/sobrecompra)
- Alineación de EMAs y SMAs
- Divergencias MACD

**⚠️ Importante:** Las señales son **informativas**, no constituyen recomendación de inversión. Son probabilidades basadas en técnica, no garantías de rendimiento.

---

## 🔧 Requisitos previos

- **Python** 3.8 o superior
- **pip** (gestor de paquetes de Python)
- Conexión a Internet (para descargar datos de Yahoo Finance)

---

## 📦 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/tu-usuario/stockwatch.git
cd stockwatch
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `streamlit` ≥1.32.0 — Framework web
- `yfinance` ≥0.2.38 — Descargador de datos Yahoo Finance
- `pandas` ≥2.0.0 — Manipulación de datos
- `numpy` ≥1.24.0 — Operaciones numéricas
- `plotly` ≥5.18.0 — Gráficos interactivos
- `ta` ≥0.11.0 — Cálculo de indicadores técnicos
- `requests` ≥2.31.0 — Cliente HTTP

### 3. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501` (por defecto).

---

## 🚀 Uso

### Página 1: 🔍 Búsqueda (Landing)

1. **Escribe un ticker o nombre** (ej: "AAPL", "Apple", "AMXL", "América Móvil")
2. **Selecciona de las sugerencias** que aparecen en tiempo real
3. Haz clic en un resultado para ir a **Análisis**

### Página 2: 📊 Análisis (Detail View)

Una vez seleccionado un ticker:

1. **Tarjeta superior**: Precio actual, cambio %, volumen, fundamentales clave
2. **Gráfico interactivo**: Velas OHLCV + indicadores superpuestos
   - Usa el selector de **timeframe** para cambiar período (1S, 1M, 3M, 6M, 1A, 3A, 5A, MAX)
   - Zoom, pan, y hover para explorar datos
3. **Tarjeta de señal**: Score, confianza, razones de la señal
4. **Tabla de indicadores**: Valores actuales de RSI, MACD, Bollinger Bands, EMAs
5. **Datos fundamentales** (si disponibles): Market cap, P/E, dividend yield, 52-week high/low, beta, sector, industria

### Página 3: ⚖️ Comparar (Comparison)

1. **Selecciona 2-5 tickers** usando los campos de entrada
2. **Compara lado a lado**:
   - Precio y cambio %
   - Volatilidad (desviación estándar)
   - Rendimiento histórico
   - Señales actuales

---

## 📁 Estructura del proyecto

```
stockwatch/
├── app.py                    # Punto de entrada Streamlit + enrutamiento
├── config.py                 # Configuración centralizada (constantes, dataclasses)
├── requirements.txt          # Dependencias Python
├── ARCHITECTURE.md           # Especificación técnica detallada
├── README.md                 # Este archivo
│
├── data/                     # Capa de datos
│   ├── __init__.py
│   ├── fetcher.py            # Wrapper yfinance + caché
│   ├── models.py             # Dataclasses de contratos
│   └── search.py             # Búsqueda de tickers
│
├── analysis/                 # Capa de análisis
│   ├── __init__.py
│   ├── indicators.py         # Cálculo de indicadores (RSI, MACD, BB, EMAs, SMAs)
│   ├── signals.py            # Generación de señales y scoring
│   ├── fundamentals.py       # Análisis fundamental
│   ├── rankings.py           # Ranking de activos
│   └── simulator.py          # Simulador de backtesting
│
└── ui/                       # Capa de UI (Streamlit)
    ├── __init__.py
    ├── search_page.py        # Página de búsqueda
    ├── detail_page.py        # Página de análisis detallado
    ├── comparison_page.py    # Página de comparación
    └── components.py         # Componentes reutilizables
```

---

## ⚙️ Configuración

Toda la configuración se centraliza en **`config.py`**:

### Mercados y activos populares
```python
MARKETS = {...}              # Definición de mercados US y MX
MX_POPULAR_STOCKS = {...}    # Sugerencias BMV
US_POPULAR_STOCKS = {...}    # Sugerencias NYSE/NASDAQ
```

### Timeframes
```python
TIMEFRAMES = {...}           # 1S, 1M, 3M, 6M, 1A, 3A, 5A, MAX
DEFAULT_TIMEFRAME = "1A"     # 1 Año por defecto
```

### Cacheo
```python
CACHE_TTL_QUOTE = 60         # 1 minuto
CACHE_TTL_OHLCV = 300        # 5 minutos
CACHE_TTL_FUNDAMENTALS = 3600 # 1 hora
CACHE_TTL_SEARCH = 1800      # 30 minutos
```

### Indicadores técnicos
```python
RSI_PERIOD = 14              # 14 periodos (estándar)
RSI_OVERSOLD = 30            # Umbral de sobreventa
RSI_OVERBOUGHT = 70          # Umbral de sobrecompra
MACD_FAST = 12, MACD_SLOW = 26, MACD_SIGNAL = 9
BB_PERIOD = 20, BB_STD = 2   # Bollinger Bands
EMA_SHORT = 20, EMA_LONG = 50
SMA_PERIODS = [20, 50, 200]
```

### Señales
```python
SIGNAL_BULLISH_THRESHOLD = 3 # Score ≥ 3 para COMPRA
SIGNAL_BEARISH_THRESHOLD = -3 # Score ≤ -3 para VENTA
SIGNAL_CONFIDENCE_HIGH = 5   # |score| ≥ 5 para Alta confianza
SIGNAL_CONFIDENCE_MED = 3    # |score| ≥ 3 para Media confianza
```

---

## 📚 Stack tecnológico

| Dependencia | Versión | Propósito |
|------------|---------|----------|
| **streamlit** | ≥1.32.0 | Framework web y UI interactiva |
| **yfinance** | ≥0.2.38 | Descarga de datos Yahoo Finance |
| **pandas** | ≥2.0.0 | Análisis y manipulación de datos |
| **numpy** | ≥1.24.0 | Operaciones numéricas y matrices |
| **plotly** | ≥5.18.0 | Gráficos interactivos (velas OHLCV) |
| **ta** | ≥0.11.0 | Indicadores técnicos (RSI, MACD, BB, etc.) |
| **requests** | ≥2.31.0 | Cliente HTTP para consultas externas |

**Lenguaje:** Python 3.8+  
**Licencia:** MIT

---

## ⚠️ Limitaciones conocidas

1. **Latencia de datos intraday**: Yahoo Finance tiene ~15 minutos de retraso en datos intradía. Para trading de corto plazo, se recomienda usar APIs de tiempo real.

2. **Disponibilidad de tickers BMV**: No todos los tickers mexicanos están disponibles en Yahoo Finance. Se recomienda verificar disponibilidad antes de agregar.

3. **Sin integración de brokers**: StockWatch es solo análisis. No se conecta a GBM, Masari, Kuspit ni otros brokers. Las órdenes deben ejecutarse manualmente en la plataforma del broker.

4. **Sin portfolio tracking en v1**: StockWatch no registra posiciones ni realiza P&L. Solo análisis de activos individuales.

5. **Datos fundamentales limitados para ETFs**: Los ETFs tienen menos datos fundamentales disponibles que las acciones comunes.

6. **Sin histórico de alertas**: Las señales no se guardan. Se generan en tiempo real cada carga.

---

## 🔒 Aviso legal

**⚠️ IMPORTANTE:** Esta aplicación es solo para fines informativos y educativos.

- **No constituye asesoría financiera.** Los indicadores técnicos son señales probabilísticas basadas en análisis matemático, **no garantías de rendimiento futuro**.
- **Inversión con riesgo.** Todo movimiento de mercado conlleva riesgo de pérdida de capital. El análisis técnico tiene limitaciones y puede fallar.
- **Responsabilidad del usuario.** El autor y contributors no asumen responsabilidad por decisiones de inversión basadas en esta herramienta.
- **Verificación necesaria.** Siempre verifica datos con fuentes oficiales antes de operar. Yahoo Finance puede tener retrasos o inexactitudes.
- **Código abierto, sin garantías.** El software se proporciona "tal cual", sin garantías de funcionamiento continuo.

**Úsalo con prudencia y responsabilidad.**

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para colaborar:

1. **Fork** el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/mi-feature`)
3. Commit tus cambios (`git commit -m 'Agregar mi feature'`)
4. Push a la rama (`git push origin feature/mi-feature`)
5. Abre un **Pull Request** describiendo tus cambios

Por favor, asegúrate de:
- Mantener el estilo de código existente
- Documentar funciones nuevas
- Probar cambios localmente antes de PR

---

## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia MIT**. Ver archivo `LICENSE` para más detalles.
