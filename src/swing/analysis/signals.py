"""Multi-factor swing trade signal detection."""

from __future__ import annotations

import pandas as pd

from swing.analysis.indicators import compute_indicators, find_support_resistance
from swing.config import (
    MIN_AVG_VOLUME,
    MIN_PRICE,
    MIN_SIGNALS_REQUIRED,
    RSI_OVERSOLD,
    SUPPORT_PROXIMITY_PCT,
    VOLUME_SURGE_FACTOR,
)
from swing.utils.logger import get_logger

log = get_logger(__name__)


def detect_signals(df: pd.DataFrame) -> dict:
    """Run all signal checks on an indicator-enriched DataFrame.

    Returns a dict with:
        - passed: bool — whether the stock qualifies
        - signals: dict[str, bool] — each primary signal status
        - signal_count: int — how many primary signals triggered
        - filters: dict[str, bool] — each filter status
        - latest: dict — latest row data for context
        - supports: list[float]
        - resistances: list[float]
    """
    if df is None or len(df) < 50:
        return {"passed": False, "reason": "insufficient_data"}

    # Compute indicators if not already present
    if "EMA_20" not in df.columns:
        df = compute_indicators(df)

    # Find support / resistance
    supports, resistances = find_support_resistance(df)

    # Get the last few rows for signal checks
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest

    # ──────────────────────── FILTERS ────────────────────────
    price_above_200ema = bool(
        pd.notna(latest.get("EMA_200")) and latest["Close"] > latest["EMA_200"]
    )
    price_min = bool(latest["Close"] >= MIN_PRICE)
    volume_min = bool(
        pd.notna(latest.get("Volume_SMA"))
        and latest["Volume_SMA"] >= MIN_AVG_VOLUME
    )

    filters = {
        "price_above_200ema": price_above_200ema,
        "price_min": price_min,
        "volume_min": volume_min,
    }

    if not all(filters.values()):
        return {
            "passed": False,
            "reason": "filter_failed",
            "filters": filters,
        }

    # ──────────────────── PRIMARY SIGNALS ────────────────────

    # Signal 1: EMA Bullish Alignment (Price > EMA 20 > EMA 50)
    ema_aligned = bool(
        pd.notna(latest.get("EMA_20"))
        and pd.notna(latest.get("EMA_50"))
        and latest["Close"] > latest["EMA_20"] > latest["EMA_50"]
    )

    # Signal 2: RSI Oversold Recovery
    # RSI was ≤ RSI_OVERSOLD within last 5 days and is now rising above it
    rsi_recovery = False
    if pd.notna(latest.get("RSI")):
        recent_rsi = df["RSI"].iloc[-5:]
        was_oversold = any(r <= RSI_OVERSOLD for r in recent_rsi.dropna())
        now_above = latest["RSI"] > RSI_OVERSOLD
        rsi_rising = latest["RSI"] > prev.get("RSI", 100) if pd.notna(prev.get("RSI")) else False
        rsi_recovery = bool(was_oversold and now_above and rsi_rising)

    # Signal 3: MACD Bullish Crossover (within last 3 days)
    macd_crossover = False
    if pd.notna(latest.get("MACD")) and pd.notna(latest.get("MACD_Signal")):
        for i in range(-3, 0):
            if abs(i) < len(df) and abs(i) - 1 < len(df):
                curr = df.iloc[i]
                prev_row = df.iloc[i - 1]
                if (
                    pd.notna(curr.get("MACD"))
                    and pd.notna(curr.get("MACD_Signal"))
                    and pd.notna(prev_row.get("MACD"))
                    and pd.notna(prev_row.get("MACD_Signal"))
                ):
                    if (
                        curr["MACD"] > curr["MACD_Signal"]
                        and prev_row["MACD"] <= prev_row["MACD_Signal"]
                    ):
                        macd_crossover = True
                        break

    # Signal 4: Support Bounce
    support_bounce = False
    if supports:
        close = latest["Close"]
        for sup in reversed(supports):
            if sup < close:
                proximity = (close - sup) / sup
                if proximity <= SUPPORT_PROXIMITY_PCT:
                    # Check if price is bouncing (today's close > yesterday's close)
                    if latest["Close"] > prev["Close"]:
                        support_bounce = True
                break

    # Signal 5: Volume Surge
    volume_surge = bool(
        pd.notna(latest.get("Volume_SMA"))
        and latest["Volume_SMA"] > 0
        and latest["Volume"] >= VOLUME_SURGE_FACTOR * latest["Volume_SMA"]
    )

    signals = {
        "ema_aligned": ema_aligned,
        "rsi_recovery": rsi_recovery,
        "macd_crossover": macd_crossover,
        "support_bounce": support_bounce,
        "volume_surge": volume_surge,
    }

    signal_count = sum(signals.values())
    passed = signal_count >= MIN_SIGNALS_REQUIRED

    return {
        "passed": passed,
        "signals": signals,
        "signal_count": signal_count,
        "filters": filters,
        "latest": {
            "close": float(latest["Close"]),
            "ema_20": float(latest["EMA_20"]) if pd.notna(latest.get("EMA_20")) else None,
            "ema_50": float(latest["EMA_50"]) if pd.notna(latest.get("EMA_50")) else None,
            "ema_200": float(latest["EMA_200"]) if pd.notna(latest.get("EMA_200")) else None,
            "rsi": float(latest["RSI"]) if pd.notna(latest.get("RSI")) else None,
            "macd": float(latest["MACD"]) if pd.notna(latest.get("MACD")) else None,
            "macd_signal": float(latest["MACD_Signal"]) if pd.notna(latest.get("MACD_Signal")) else None,
            "atr": float(latest["ATR"]) if pd.notna(latest.get("ATR")) else None,
            "volume": float(latest["Volume"]),
            "volume_sma": float(latest["Volume_SMA"]) if pd.notna(latest.get("Volume_SMA")) else None,
        },
        "supports": supports,
        "resistances": resistances,
    }
