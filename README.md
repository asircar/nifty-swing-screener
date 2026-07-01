# 📊 Multi-Market Swing Trading Screener

**Swing Trading Stock Screener for Indian (Nifty 50/100/200/500) and US (Dow 30/Nasdaq 100/S&P 500) Stock Markets**

Nifty Swing Screener scans multiple indices for swing trading opportunities using multi-factor technical analysis. It identifies stocks exhibiting bullish signals, computes volatility-anchored trade entry/exit levels, and ranks candidates with a transparent, explainable scoring system.

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Multi-Factor Signal Detection** — EMA Alignment, RSI Recovery, MACD Crossover, Support Bounce, Volume Surge
- **Explainable Scoring** — Click any score badge on the web dashboard to see a full breakdown of weighted factors
- **Volatility-Anchored Levels** — Automated stop-losses and targets scaled directly to daily volatility (ATR) to ensure trades resolve within the swing trading boundary (3 to 7 trading days)
- **Interactive Dashboard** — Real-time filtering, sorting, sparkline charts, and responsive design
- **Scan Scope Control** — Scan Nifty or US indices with estimated completion times
- **Smart Caching** — SQLite-based OHLCV cache to avoid redundant API calls
- **CLI + Web** — Full-featured CLI with Rich tables, or a web dashboard via FastAPI

---

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
│   ├── nifty_indices.py  # NSE India stock list fetcher
│   └── us_stocks.py      # US stock list fetcher
├── utils/
│   └── logger.py         # Logging setup
├── web/
│   ├── app.py            # FastAPI application
│   └── static/           # Dashboard (HTML, CSS, JS)
├── config.py             # All configurable parameters
└── main.py               # CLI entry point
```

---

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
uv run swing --web
# Open http://localhost:8000
```

### Run the CLI Screener

```bash
# Scan all Nifty 500 stocks (default)
uv run swing

# Scan a specific market index
uv run swing -m nifty_50
# Available: nifty_50, nifty_100, nifty_200, nifty_500, dow_30, nasdaq_100, sp_500

# Scan only first 10 stocks (faster testing)
uv run swing -n 10
```

---

## 📈 How It Works

### 1. Filters (must pass all)
| Filter | Criteria |
|--------|----------|
| Trend | Price > 200-day EMA |
| Volume | Average daily volume ≥ 100K shares |
| Price | Stock price ≥ ₹50 (India) or ≥ $5 (US) |

### 2. Signals (need ≥ 2 to qualify)
| Signal | Logic |
|--------|-------|
| **EMA Alignment** | Price > EMA 20 > EMA 50 (bullish structure) |
| **RSI Recovery** | RSI was ≤ 40 in last 5 days, now rising above 40 |
| **MACD Crossover** | MACD crossed above signal line within 3 days |
| **Support Bounce** | Price within 2% of a support level and rising |
| **Volume Surge** | Today's volume ≥ 1.5× the 20-day average on a positive close (green day) |

### 3. Trade Levels (Volatility-Anchored)
To keep trades within a short-term swing boundary, levels are anchored to the Average True Range (ATR):
- **Entry**: Current closing price.
- **Stop Loss**: `Entry - 1.2 × ATR` (Tight but realistic daily volatility filter).
- **Target 1 (Core)**: `Entry + 1.5 × ATR` (Quick 2–4 day target).
- **Target 2 (Runner)**: `Entry + 2.5 × ATR` (Extended 4–7 day target).
- **Risk:Reward**: Filters out setups failing to yield a `1.5` R:R ratio against the primary target (Target 2).

### 4. Scoring (0–100, weighted)
| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Signal Count | 30% | How many signals fired (out of 5) |
| Risk/Reward | 25% | Quality of the R:R ratio (4.0 = perfect) |
| Volume | 15% | Volume relative to average |
| Trend Strength | 15% | EMA alignment (Price > EMA20 > EMA50 > EMA200) |
| RSI Position | 15% | Whether RSI is in the ideal 40–60 swing zone (not penalized above 70 during strong trends) |

---

## ⚙️ Configuration

All parameters are in `src/swing/config.py`:

```python
EMA_SHORT = 20            # Short-term EMA
EMA_MID = 50              # Medium-term EMA
EMA_LONG = 200            # Long-term EMA
RSI_PERIOD = 14           # RSI lookback
MIN_SIGNALS_REQUIRED = 2  # Minimum signals to qualify
ATR_SL_MULTIPLIER = 1.2   # Stop loss = entry − 1.2 × ATR
ATR_T1_MULTIPLIER = 1.5   # Target 1 = entry + 1.5 × ATR
ATR_T2_MULTIPLIER = 2.5   # Target 2 = entry + 2.5 × ATR
MIN_RISK_REWARD = 1.5     # Minimum risk:reward ratio
```

---

## ⚠️ Disclaimer

This tool is for **educational purposes only**. It is not financial advice. Always do your own research before making any trading decisions.

---

## 📄 License

MIT
