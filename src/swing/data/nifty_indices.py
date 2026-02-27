"""Fetch and maintain the Nifty 500 stock list."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import httpx

from swing.config import (
    FALLBACK_CSV,
    NIFTY100_CSV_URL,
    NIFTY100_FALLBACK_CSV,
    NIFTY200_CSV_URL,
    NIFTY200_FALLBACK_CSV,
    NIFTY500_CSV_URL,
    NIFTY50_CSV_URL,
    NIFTY50_FALLBACK_CSV,
)
from swing.utils.logger import get_logger

log = get_logger(__name__)


def _download_index_csv(csv_url: str) -> str | None:
    """Download an index constituent CSV from NSE India."""
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
            resp = client.get(csv_url, headers=headers)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        log.warning("Failed to download CSV from NSE (%s): %s", csv_url, exc)
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


def _save_fallback(csv_text: str, fallback_path: Path) -> None:
    """Save downloaded CSV as fallback."""
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_path.write_text(csv_text, encoding="utf-8")
    log.info("Saved fallback CSV at %s", fallback_path)


def _load_fallback(fallback_path: Path) -> list[dict]:
    """Load stocks from fallback CSV."""
    if not fallback_path.exists():
        log.error("No fallback CSV found at %s", fallback_path)
        return []
    log.info("Loading stocks from fallback CSV: %s", fallback_path.name)
    csv_text = fallback_path.read_text(encoding="utf-8")
    return _parse_csv_text(csv_text)


def _get_index_stocks(
    name: str,
    csv_url: str,
    fallback_path: Path,
    min_expected_count: int,
) -> list[dict]:
    """Return stock universe for an NSE index from live CSV or fallback."""
    csv_text = _download_index_csv(csv_url)
    if csv_text:
        stocks = _parse_csv_text(csv_text)
        if len(stocks) >= min_expected_count:
            _save_fallback(csv_text, fallback_path)
            log.info("Loaded %d stocks for %s from NSE India", len(stocks), name)
            return stocks
        log.warning(
            "Downloaded %s CSV had only %d stocks (expected >= %d), using fallback",
            name,
            len(stocks),
            min_expected_count,
        )
    return _load_fallback(fallback_path)


def get_nifty50_stocks() -> list[dict]:
    """Return Nifty 50 constituents."""
    return _get_index_stocks(
        name="Nifty 50",
        csv_url=NIFTY50_CSV_URL,
        fallback_path=NIFTY50_FALLBACK_CSV,
        min_expected_count=45,
    )


def get_nifty100_stocks() -> list[dict]:
    """Return Nifty 100 constituents."""
    return _get_index_stocks(
        name="Nifty 100",
        csv_url=NIFTY100_CSV_URL,
        fallback_path=NIFTY100_FALLBACK_CSV,
        min_expected_count=90,
    )


def get_nifty200_stocks() -> list[dict]:
    """Return Nifty 200 constituents."""
    return _get_index_stocks(
        name="Nifty 200",
        csv_url=NIFTY200_CSV_URL,
        fallback_path=NIFTY200_FALLBACK_CSV,
        min_expected_count=180,
    )


def get_nifty500_stocks() -> list[dict]:
    """Return Nifty 500 constituents."""
    return _get_index_stocks(
        name="Nifty 500",
        csv_url=NIFTY500_CSV_URL,
        fallback_path=FALLBACK_CSV,
        min_expected_count=400,
    )
