"""Fetch stock lists for US market indices (S&P 500, Dow 30, Nasdaq 100)."""

from __future__ import annotations

from io import StringIO

import httpx
import pandas as pd

from swing.utils.logger import get_logger

log = get_logger(__name__)

_WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
_WIKI_DOW30 = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
_WIKI_NASDAQ100 = "https://en.wikipedia.org/wiki/Nasdaq-100"

_HEADERS = {
    "User-Agent": "SwingScreenerBot/1.0 (https://github.com/asircar/nifty-swing-screener)"
}


def _fetch_wiki_tables(url: str) -> list[pd.DataFrame]:
    """Fetch HTML from Wikipedia and parse tables."""
    resp = httpx.get(url, headers=_HEADERS, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    return pd.read_html(StringIO(resp.text))


def _safe_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find first matching column name from candidates."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def get_sp500_stocks() -> list[dict]:
    """Get S&P 500 stocks from Wikipedia."""
    try:
        tables = _fetch_wiki_tables(_WIKI_SP500)
        df = tables[0]

        sym_col = _safe_col(df, ["Symbol", "Ticker symbol", "Ticker"])
        name_col = _safe_col(df, ["Security", "Company"])
        sector_col = _safe_col(df, ["GICS Sector", "Sector", "Industry"])

        if not sym_col or not name_col:
            log.error("S&P 500 table: unexpected columns: %s", list(df.columns))
            return []

        stocks = []
        for _, row in df.iterrows():
            symbol = str(row[sym_col]).strip().replace(".", "-")
            stocks.append({
                "symbol": symbol,
                "company": str(row[name_col]).strip(),
                "industry": str(row.get(sector_col, "")).strip() if sector_col else "",
                "yf_ticker": symbol,
            })

        log.info("Loaded %d S&P 500 stocks from Wikipedia", len(stocks))
        return stocks
    except Exception as exc:
        log.error("Failed to fetch S&P 500 list: %s", exc)
        return []


def get_dow30_stocks() -> list[dict]:
    """Get Dow Jones 30 stocks from Wikipedia."""
    try:
        tables = _fetch_wiki_tables(_WIKI_DOW30)

        df = None
        for table in tables:
            if "Symbol" in table.columns:
                df = table
                break

        if df is None:
            log.error("Could not find Dow 30 components table")
            return []

        sym_col = _safe_col(df, ["Symbol", "Ticker"])
        name_col = _safe_col(df, ["Company"])
        sector_col = _safe_col(df, ["Industry", "Sector"])

        if not sym_col or not name_col:
            log.error("Dow 30 table: unexpected columns: %s", list(df.columns))
            return []

        stocks = []
        for _, row in df.iterrows():
            symbol = str(row[sym_col]).strip()
            stocks.append({
                "symbol": symbol,
                "company": str(row[name_col]).strip(),
                "industry": str(row.get(sector_col, "")).strip() if sector_col else "",
                "yf_ticker": symbol,
            })

        log.info("Loaded %d Dow Jones stocks from Wikipedia", len(stocks))
        return stocks
    except Exception as exc:
        log.error("Failed to fetch Dow 30 list: %s", exc)
        return []


def get_nasdaq100_stocks() -> list[dict]:
    """Get Nasdaq 100 stocks from Wikipedia."""
    try:
        tables = _fetch_wiki_tables(_WIKI_NASDAQ100)

        df = None
        for table in tables:
            if "Ticker" in table.columns:
                df = table
                break

        if df is None:
            log.error("Could not find Nasdaq 100 components table")
            return []

        sym_col = _safe_col(df, ["Ticker", "Symbol"])
        name_col = _safe_col(df, ["Company", "Security"])
        sector_col = _safe_col(df, ["GICS Sector", "Sector", "Industry"])

        if not sym_col or not name_col:
            log.error("Nasdaq 100 table: unexpected columns: %s", list(df.columns))
            return []

        stocks = []
        for _, row in df.iterrows():
            symbol = str(row[sym_col]).strip()
            stocks.append({
                "symbol": symbol,
                "company": str(row[name_col]).strip(),
                "industry": str(row.get(sector_col, "")).strip() if sector_col else "",
                "yf_ticker": symbol,
            })

        log.info("Loaded %d Nasdaq 100 stocks from Wikipedia", len(stocks))
        return stocks
    except Exception as exc:
        log.error("Failed to fetch Nasdaq 100 list: %s", exc)
        return []
