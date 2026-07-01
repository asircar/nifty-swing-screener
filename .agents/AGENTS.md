# Nifty Swing Screener - Project Instructions

## 📊 Overview

Nifty Swing Screener is a multi-market swing trading stock screener written in Python. It scans Indian stock markets (Nifty 50, 100, 200, 500) and US stock markets (Dow 30, Nasdaq 100, S&P 500) to identify swing trading opportunities.

It uses:
- **Technical Indicators**: EMAs (20, 50, 200), RSI, MACD, ATR, and local support/resistance swing high/low clustering.
- **Bullish Factors**: EMA alignment, RSI recovery (oversold recovery), MACD bullish crossover, Support bounce, and Volume surge.
- **Risk Management**: ATR-based automated entry, stop-loss, and profit targets with a risk-to-reward filter.
- **Weighted Scoring**: Multi-factor scoring from 0 to 100 to rank candidates.
- **FastAPI Web Dashboard**: Rich browser-based interface to display results, charts, and details.

---

## 🛠️ Tooling & Environment

- **Python Version**: `>=3.12` (managed via `.python-version`)
- **Package & Env Management**: [Astral uv](https://docs.astral.sh/uv/)
- **Core Dependencies**:
  - `yfinance` - OHLCV data retrieval.
  - `pandas` & `numpy` - Vectorized calculations.
  - `ta` - Technical analysis library.
  - `fastapi` & `uvicorn` - Web dashboard server.
  - `rich` - Beautiful CLI formatting and console output.
  - `sqlite3` - Local SQLite cache under `/tmp/swing/cache.db` to persist historical daily data and avoid redundant API requests.

---

## 🚀 Key Commands

All commands should be run using `uv` to ensure proper virtual environment execution:

*   **Install Dependencies**:
    ```bash
    uv sync
    ```
*   **Run CLI Screener** (Defaults to `nifty_500`):
    ```bash
    uv run swing
    ```
*   **Run CLI for Specific Market**:
    ```bash
    uv run swing -m <market>
    # Available markets: nifty_50, nifty_100, nifty_200, nifty_500, dow_30, nasdaq_100, sp_500
    ```
*   **Run CLI with Stock Scan Limit** (useful for rapid testing):
    ```bash
    uv run swing -n <limit>
    ```
*   **Run Web Dashboard Server**:
    ```bash
    uv run swing --web
    ```
*   **Run Tests**:
    ```bash
    uv run pytest
    ```

---

## 📂 Codebase Reference

- **Configuration**: [config.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/config.py)
  - Contains paths, fallback CSV files, indicator window lengths, signal thresholds, and scoring weights.
- **CLI & Web App Orchestrator**: [main.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/main.py)
  - Directs terminal flow or launches the FastAPI server.
- **Analysis Modules**:
  - [indicators.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/analysis/indicators.py): Vectorized indicator computations and support/resistance clustering algorithms.
  - [signals.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/analysis/signals.py): Qualifying filters (trend, minimum price, average daily volume) and signal checks.
  - [levels.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/analysis/levels.py): Calculations for entry, stop loss, targets, and risk-reward ratio.
  - [scorer.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/analysis/scorer.py): Weighted 0-100 scoring logic.
- **Data Modules**:
  - [fetcher.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/data/fetcher.py): SQLite-cached daily data download.
  - [cache.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/data/cache.py): Local cache clean-up and query execution.
  - [nifty_indices.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/data/nifty_indices.py) & [us_stocks.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/data/us_stocks.py): Utilities for loading stock index symbols (with offline CSV fallbacks).
- **Web App**:
  - [app.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/web/app.py): FastAPI endpoints.
  - [static/](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/web/static/): Dashboard client pages (HTML, CSS, JS).

---

## 🎨 Development Guidelines

1.  **Maintain Vectorized Calculations**:
    - Do not iterate row-by-row for technical indicator computations. Use Pandas/Numpy built-ins and the `ta` library to ensure scans complete rapidly.
2.  **Respect Caching Layer**:
    - Always query historical data via the cache (`fetch_ohlcv`) to protect against API rate limits and keep scans efficient.
3.  **Config First**:
    - Avoid hardcoding indicator sizes, weights, or signal thresholds. Refer to or update constants defined in [config.py](file:///Users/arunava/Projects/nifty-swing-screener/src/swing/config.py).
4.  **Premium Frontend Styling**:
    - The FastAPI web dashboard is a key user-facing feature. Any UI updates should prioritize clean typography, high-quality dark mode palettes, vibrant interactive signals, and mobile responsiveness using native CSS features.
5.  **Preserve Offline Fallbacks**:
    - Ensure index fetching code has reliable fallback paths to local CSV files in the data directory in case NSE/archives sites are unreachable.
