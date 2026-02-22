"""Scoring and ranking engine for swing trade candidates."""

from __future__ import annotations

from swing.config import MIN_RISK_REWARD, SCORE_WEIGHTS, VOLUME_SURGE_FACTOR


def compute_score(signal_result: dict, levels: dict) -> dict:
    """Compute a 0–100 Swing Score with full explainable breakdown.

    Returns a dict with:
        - total: float (0–100)
        - factors: list of dicts with name, raw_score, weight, weighted, reason
    """
    signals = signal_result.get("signals", {})
    latest = signal_result.get("latest", {})

    # ── Factor 1: Signal count (0–100) ──
    signal_count = sum(signals.values())
    max_signals = len(signals)  # 5
    signal_score = (signal_count / max_signals) * 100
    active = [k for k, v in signals.items() if v]
    signal_reason = f"{signal_count}/{max_signals} signals active"

    # ── Factor 2: Risk-reward ratio quality (0–100) ──
    rr = levels.get("risk_reward", MIN_RISK_REWARD)
    rr_score = min(100, (rr / 4.0) * 100)
    rr_reason = f"R:R = {rr:.1f} (4.0 = perfect)"

    # ── Factor 3: Volume confirmation (0–100) ──
    volume = latest.get("volume", 0)
    volume_sma = latest.get("volume_sma", 1)
    if volume_sma and volume_sma > 0:
        vol_ratio = volume / volume_sma
        vol_score = min(100, (vol_ratio / (VOLUME_SURGE_FACTOR * 2)) * 100)
        vol_reason = f"Volume is {vol_ratio:.1f}× avg"
    else:
        vol_score = 0
        vol_ratio = 0
        vol_reason = "No volume data"

    # ── Factor 4: Trend strength — EMA alignment (0–100) ──
    trend_score = 0
    trend_parts = []
    close = latest.get("close", 0)
    ema_20 = latest.get("ema_20")
    ema_50 = latest.get("ema_50")
    ema_200 = latest.get("ema_200")

    if ema_20 and close > ema_20:
        trend_score += 33
        trend_parts.append("Price > EMA20")
    if ema_50 and ema_20 and ema_20 > ema_50:
        trend_score += 33
        trend_parts.append("EMA20 > EMA50")
    if ema_200 and ema_50 and ema_50 > ema_200:
        trend_score += 34
        trend_parts.append("EMA50 > EMA200")
    trend_reason = ", ".join(trend_parts) if trend_parts else "Weak trend alignment"

    # ── Factor 5: RSI positioning (0–100) ──
    rsi = latest.get("rsi", 50)
    if rsi is None:
        rsi = 50
    if 40 <= rsi <= 60:
        rsi_score = 100
        rsi_reason = f"RSI {rsi:.0f} — ideal swing zone (40–60)"
    elif 30 <= rsi < 40 or 60 < rsi <= 70:
        rsi_score = 70
        rsi_reason = f"RSI {rsi:.0f} — acceptable range"
    elif rsi < 30:
        rsi_score = 40
        rsi_reason = f"RSI {rsi:.0f} — deeply oversold, may signal weakness"
    else:
        rsi_score = max(0, 100 - (rsi - 70) * 5)
        rsi_reason = f"RSI {rsi:.0f} — overbought territory"

    # ── Weighted composite ──
    factors = [
        {
            "name": "Signal Count",
            "raw_score": round(signal_score, 1),
            "weight": SCORE_WEIGHTS["signals"],
            "weighted": round(signal_score * SCORE_WEIGHTS["signals"], 1),
            "reason": signal_reason,
        },
        {
            "name": "Risk / Reward",
            "raw_score": round(rr_score, 1),
            "weight": SCORE_WEIGHTS["risk_reward"],
            "weighted": round(rr_score * SCORE_WEIGHTS["risk_reward"], 1),
            "reason": rr_reason,
        },
        {
            "name": "Volume",
            "raw_score": round(vol_score, 1),
            "weight": SCORE_WEIGHTS["volume"],
            "weighted": round(vol_score * SCORE_WEIGHTS["volume"], 1),
            "reason": vol_reason,
        },
        {
            "name": "Trend Strength",
            "raw_score": round(trend_score, 1),
            "weight": SCORE_WEIGHTS["trend"],
            "weighted": round(trend_score * SCORE_WEIGHTS["trend"], 1),
            "reason": trend_reason,
        },
        {
            "name": "RSI Position",
            "raw_score": round(rsi_score, 1),
            "weight": SCORE_WEIGHTS["rsi"],
            "weighted": round(rsi_score * SCORE_WEIGHTS["rsi"], 1),
            "reason": rsi_reason,
        },
    ]

    total = round(min(100, max(0, sum(f["weighted"] for f in factors))), 1)

    return {"total": total, "factors": factors}


def rank_candidates(candidates: list[dict]) -> list[dict]:
    """Sort candidates by swing score (highest first)."""
    return sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
