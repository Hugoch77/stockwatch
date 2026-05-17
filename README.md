# 📈 StockWatch — Análisis de Inversión Local

App local para analizar acciones y ETFs de mercados de **México (BMV)** y **Estados Unidos (NYSE/NASDAQ)**.
Diseñada para inversores de **GBM** y mercados similares.

## Instalación

```bash
cd stockwatch
pip install -r requirements.txt
streamlit run app.py
```

## Uso

1. Escribe el ticker o nombre de una empresa en el buscador
2. Selecciona el activo para ver el análisis completo
3. Explora indicadores técnicos, datos fundamentales y señales de inversión

## Mercados soportados

| Mercado | Ejemplos |
|---------|---------|
| 🇺🇸 USA | AAPL, MSFT, SPY, QQQ, NVDA |
| 🇲🇽 México (BMV) | AMXL.MX, GFNORTEO.MX, CEMEXCPO.MX |

## Fuentes de datos

- **Yahoo Finance** (yfinance) — gratuito, sin API key

## ⚠️ Aviso legal

Esta aplicación es solo para fines informativos. No constituye asesoría financiera.
Los indicadores técnicos son señales probabilísticas, no garantías de rendimiento.
