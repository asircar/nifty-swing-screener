"""Download OHLCV data via yfinance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from swing.config import HISTORY_PERIOD
from swing.data.cache import get_cached_data, save_to_cache
from swing.utils.logger import get_logger

log = get_logger(__name__)


def fetch_ohlcv(ticker: str, use_cache: bool = True) -> pd.DataFrame | None:
    """Fetch daily OHLCV data for a single ticker.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume
    Index is DatetimeIndex. Returns None on failure.
    """
    # Check cache first
    if use_cache:
        cached = get_cached_data(ticker)
        if cached is not None and len(cached) > 50:
            return cached

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=HISTORY_PERIOD, interval="1d")

        if df is None or df.empty or len(df) < 50:
            log.warning("Insufficient data for %s (%d rows)", ticker, len(df) if df is not None else 0)
            return None

        # Keep only the columns we need
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)

        # Cache the result
        if use_cache and len(df) > 50:
            save_to_cache(ticker, df)

        return df

    except Exception as exc:
        log.warning("Failed to fetch data for %s: %s", ticker, exc)
        return None


def fetch_batch(
    tickers: list[str],
    use_cache: bool = True,
    progress_callback=None,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data for a batch of tickers.

    Returns a dict mapping ticker -> DataFrame.
    Skips tickers that fail or have insufficient data.
    """
    results: dict[str, pd.DataFrame] = {}
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        df = fetch_ohlcv(ticker, use_cache=use_cache)
        if df is not None:
            results[ticker] = df

        if progress_callback:
            progress_callback(i, total, ticker)

    log.info("Fetched data for %d / %d tickers", len(results), total)
    return results
