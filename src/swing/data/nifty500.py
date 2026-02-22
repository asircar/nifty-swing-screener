"""Fetch and maintain the Nifty 500 stock list."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import httpx
import pandas as pd

from swing.config import FALLBACK_CSV, NIFTY500_CSV_URL
from swing.utils.logger import get_logger

log = get_logger(__name__)


def _download_nifty500_csv() -> str | None:
    """Download the Nifty 500 CSV from NSE India."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,text/plain,*/*",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            # Hit NSE homepage first to get cookies
            client.get("https://www.nseindia.com/", headers=headers)
            resp = client.get(NIFTY500_CSV_URL, headers=headers)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        log.warning("Failed to download Nifty 500 list from NSE: %s", exc)
        return None


def _parse_csv_text(csv_text: str) -> list[dict]:
    """Parse the NSE CSV text into a list of stock dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    stocks = []
    for row in reader:
        # NSE CSV columns: Company Name, Industry, Symbol, Series, ISIN Code
        symbol = row.get("Symbol", "").strip()
        company = row.get("Company Name", "").strip()
        industry = row.get("Industry", "").strip()
        if symbol:
            stocks.append(
                {
                    "symbol": symbol,
                    "company": company,
                    "industry": industry,
                    "yf_ticker": f"{symbol}.NS",
                }
            )
    return stocks


def _save_fallback(csv_text: str) -> None:
    """Save downloaded CSV as fallback."""
    FALLBACK_CSV.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_CSV.write_text(csv_text, encoding="utf-8")
    log.info("Saved fallback CSV at %s", FALLBACK_CSV)


def _load_fallback() -> list[dict]:
    """Load stocks from fallback CSV."""
    if not FALLBACK_CSV.exists():
        log.error("No fallback CSV found at %s", FALLBACK_CSV)
        return []
    log.info("Loading stocks from fallback CSV")
    csv_text = FALLBACK_CSV.read_text(encoding="utf-8")
    return _parse_csv_text(csv_text)


def get_nifty500_stocks() -> list[dict]:
    """Return list of Nifty 500 stocks with symbol, company, industry, yf_ticker.

    Tries to download fresh list from NSE. Falls back to local CSV.
    """
    csv_text = _download_nifty500_csv()
    if csv_text:
        stocks = _parse_csv_text(csv_text)
        if len(stocks) >= 400:  # sanity check
            _save_fallback(csv_text)
            log.info("Loaded %d stocks from NSE India", len(stocks))
            return stocks
        log.warning("Downloaded CSV had only %d stocks, using fallback", len(stocks))

    return _load_fallback()
