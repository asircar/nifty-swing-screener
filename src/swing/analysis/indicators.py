"""Compute technical indicators on OHLCV data."""

from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

from swing.config import (
    ATR_PERIOD,
    EMA_LONG,
    EMA_MID,
    EMA_SHORT,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    RSI_PERIOD,
    VOLUME_SMA_PERIOD,
)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicator columns to the OHLCV DataFrame.

    Input must have columns: Open, High, Low, Close, Volume
    Returns the DataFrame with added indicator columns.
    """
    df = df.copy()

    # ── EMAs ──
    df["EMA_20"] = EMAIndicator(close=df["Close"], window=EMA_SHORT).ema_indicator()
    df["EMA_50"] = EMAIndicator(close=df["Close"], window=EMA_MID).ema_indicator()
    df["EMA_200"] = EMAIndicator(close=df["Close"], window=EMA_LONG).ema_indicator()

    # ── RSI ──
    df["RSI"] = RSIIndicator(close=df["Close"], window=RSI_PERIOD).rsi()

    # ── MACD ──
    macd = MACD(
        close=df["Close"],
        window_slow=MACD_SLOW,
        window_fast=MACD_FAST,
        window_sign=MACD_SIGNAL,
    )
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Hist"] = macd.macd_diff()

    # ── ATR ──
    df["ATR"] = AverageTrueRange(
        high=df["High"], low=df["Low"], close=df["Close"], window=ATR_PERIOD
    ).average_true_range()

    # ── Volume SMA ──
    df["Volume_SMA"] = df["Volume"].rolling(window=VOLUME_SMA_PERIOD).mean()

    return df


def find_support_resistance(
    df: pd.DataFrame, lookback: int = 60, tolerance: float = 0.015
) -> tuple[list[float], list[float]]:
    """Find support and resistance levels from swing highs/lows.

    Uses a rolling window to detect local minima (supports) and
    local maxima (resistances). Clusters nearby levels.

    Returns (supports, resistances) as sorted lists of price levels.
    """
    if len(df) < lookback:
        lookback = max(20, len(df) - 5)

    recent = df.tail(lookback)
    highs = recent["High"].values
    lows = recent["Low"].values

    window = 5  # bars on each side to qualify as swing point

    supports_raw: list[float] = []
    resistances_raw: list[float] = []

    for i in range(window, len(lows) - window):
        # Swing low → support
        if lows[i] == min(lows[i - window : i + window + 1]):
            supports_raw.append(float(lows[i]))
        # Swing high → resistance
        if highs[i] == max(highs[i - window : i + window + 1]):
            resistances_raw.append(float(highs[i]))

    # Cluster nearby levels
    supports = _cluster_levels(supports_raw, tolerance)
    resistances = _cluster_levels(resistances_raw, tolerance)

    return sorted(supports), sorted(resistances)


def _cluster_levels(levels: list[float], tolerance: float) -> list[float]:
    """Merge nearby price levels within tolerance %."""
    if not levels:
        return []

    levels = sorted(levels)
    clusters: list[list[float]] = [[levels[0]]]

    for lvl in levels[1:]:
        if abs(lvl - clusters[-1][-1]) / clusters[-1][-1] <= tolerance:
            clusters[-1].append(lvl)
        else:
            clusters.append([lvl])

    return [sum(c) / len(c) for c in clusters]
