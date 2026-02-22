"""SQLite caching layer for OHLCV data."""

from __future__ import annotations

import sqlite3
from datetime import date

import pandas as pd

from swing.config import DB_PATH
from swing.utils.logger import get_logger

log = get_logger(__name__)


def _get_conn() -> sqlite3.Connection:
    """Get a connection to the cache database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv_cache (
            ticker TEXT NOT NULL,
            fetch_date TEXT NOT NULL,
            data_json TEXT NOT NULL,
            PRIMARY KEY (ticker, fetch_date)
        )
    """)
    conn.commit()
    return conn


def get_cached_data(ticker: str) -> pd.DataFrame | None:
    """Return cached OHLCV DataFrame for ticker if fetched today, else None."""
    today = date.today().isoformat()
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT data_json FROM ohlcv_cache WHERE ticker = ? AND fetch_date = ?",
            (ticker, today),
        ).fetchone()
        if row is None:
            return None
        df = pd.read_json(row[0], orient="split")
        return df
    except Exception:
        return None
    finally:
        conn.close()


def save_to_cache(ticker: str, df: pd.DataFrame) -> None:
    """Save OHLCV DataFrame to cache for today."""
    today = date.today().isoformat()
    conn = _get_conn()
    try:
        data_json = df.to_json(orient="split", date_format="iso")
        conn.execute(
            """INSERT OR REPLACE INTO ohlcv_cache (ticker, fetch_date, data_json)
               VALUES (?, ?, ?)""",
            (ticker, today, data_json),
        )
        conn.commit()
    except Exception as exc:
        log.warning("Failed to cache data for %s: %s", ticker, exc)
    finally:
        conn.close()


def clear_old_cache(keep_days: int = 3) -> None:
    """Remove cache entries older than keep_days."""
    from datetime import timedelta

    cutoff = (date.today() - timedelta(days=keep_days)).isoformat()
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM ohlcv_cache WHERE fetch_date < ?", (cutoff,))
        conn.commit()
    except Exception as exc:
        log.warning("Failed to clear old cache: %s", exc)
    finally:
        conn.close()
