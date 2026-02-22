# 📊 Nifty Swing Screener

**Swing Trading Stock Screener for the Indian Stock Market (Nifty 500)**

Nifty Swing Screener scans the Nifty 500 universe for swing trading opportunities using multi-factor technical analysis. It identifies stocks exhibiting bullish signals, computes trade entry/exit levels, and ranks candidates with a transparent, explainable scoring system.

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Multi-Factor Signal Detection** — EMA Alignment, RSI Recovery, MACD Crossover, Support Bounce, Volume Surge
- **Explainable Scoring** — Click any score badge to see a full breakdown of weighted factors
- **Trade Levels** — Automated entry, stop-loss (ATR + support-based), and profit targets with risk:reward ratios
- **Interactive Dashboard** — Real-time filtering, sorting, sparkline charts, and responsive design
- **Scan Scope Control** — Scan Nifty 50 / 100 / 200 / 500 stocks with estimated completion times
- **Smart Caching** — SQLite-based OHLCV cache to avoid redundant API calls
- **CLI + Web** — Full-featured CLI with Rich tables, or a web dashboard via FastAPI

## 🏗️ Architecture

```
src/swing/
├── analysis/
│   ├── indicators.py     # EMA, RSI, MACD, ATR, Support/Resistance
│   ├── signals.py        # Multi-factor signal detection + filters
│   ├── scorer.py         # 0-100 weighted scoring with breakdown
│   └── levels.py         # Entry, stop-loss, target calculations
├── data/
│   ├── fetcher.py        # yfinance OHLCV downloader with caching
│   ├── cache.py          # SQLite caching layer
│   └── nifty500.py       # NSE India stock list fetcher
├── utils/
│   └── logger.py         # Logging setup
├── web/
│   ├── app.py            # FastAPI application
│   └── static/           # Dashboard (HTML, CSS, JS)
├── config.py             # All configurable parameters
└── main.py               # CLI entry point
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/asircar/nifty-swing-screener.git
cd nifty-swing-screener

# Install with uv
uv sync
```

### Run the Web Dashboard

```bash
uv run python -m swing.main --web
# Open http://localhost:8000
```

### Run the CLI Screener

```bash
# Scan all Nifty 500 stocks
uv run swing

# Scan only first 50 stocks (faster)
uv run swing -n 50
```

## 📈 How It Works

### 1. Filters (must pass all)
| Filter | Criteria |
|--------|----------|
| Trend | Price > 200-day EMA |
| Volume | Average daily volume ≥ 100K shares |
| Price | Stock price ≥ ₹50 |

### 2. Signals (need ≥ 2 to qualify)
| Signal | Logic |
|--------|-------|
| **EMA Alignment** | Price > EMA 20 > EMA 50 (bullish structure) |
| **RSI Recovery** | RSI was ≤ 40 in last 5 days, now rising above 40 |
| **MACD Crossover** | MACD crossed above signal line within 3 days |
| **Support Bounce** | Price within 2% of a support level and rising |
| **Volume Surge** | Today's volume ≥ 1.5× the 20-day average |

### 3. Scoring (0–100, weighted)
| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Signal Count | 30% | How many signals fired (out of 5) |
| Risk/Reward | 25% | Quality of the R:R ratio (4.0 = perfect) |
| Volume | 15% | Volume relative to average |
| Trend Strength | 15% | EMA alignment (Price > EMA20 > EMA50 > EMA200) |
| RSI Position | 15% | Whether RSI is in the ideal 40–60 swing zone |

## ⚙️ Configuration

All parameters are in `src/swing/config.py`:

```python
EMA_SHORT = 20            # Short-term EMA
EMA_MID = 50              # Medium-term EMA
EMA_LONG = 200            # Long-term EMA
RSI_PERIOD = 14           # RSI lookback
MIN_SIGNALS_REQUIRED = 2  # Minimum signals to qualify
ATR_SL_MULTIPLIER = 1.5   # Stop loss = entry − 1.5 × ATR
MIN_RISK_REWARD = 2.0     # Minimum risk:reward ratio
```

## ⚠️ Disclaimer

This tool is for **educational purposes only**. It is not financial advice. Always do your own research before making any trading decisions.

## 📄 License

MIT
