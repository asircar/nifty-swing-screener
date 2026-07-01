"""Calculate entry, target, and stop-loss levels."""

from __future__ import annotations

from swing.config import ATR_SL_MULTIPLIER, ATR_T1_MULTIPLIER, ATR_T2_MULTIPLIER, MIN_RISK_REWARD


def compute_levels(signal_result: dict) -> dict | None:
    """Compute entry, stop-loss, and target levels for a swing candidate.

    Takes the output from detect_signals() and returns levels,
    or None if risk-reward is insufficient.

    Returns dict with:
        - entry: float
        - stop_loss: float
        - target_1: float
        - target_2: float
        - risk: float
        - reward: float
        - risk_reward: float
    """
    latest = signal_result.get("latest", {})

    close = latest.get("close")
    atr = latest.get("atr")

    if close is None or atr is None or atr <= 0:
        return None

    # ── Entry ──
    # Strictly use the closing price as entry point
    entry = close

    # ── Stop Loss ──
    # ATR-based: entry − 1.2 × ATR
    stop_loss = entry - ATR_SL_MULTIPLIER * atr

    # ── Targets ──
    risk = entry - stop_loss
    if risk <= 0:
        return None

    # Target 1: Core Target (1.5 × ATR)
    target_1 = entry + ATR_T1_MULTIPLIER * atr

    # Target 2: Runner Target (2.5 × ATR)
    target_2 = entry + ATR_T2_MULTIPLIER * atr

    # Primary Target is the Runner Target for risk-reward calculations
    primary_target = target_2
    reward = primary_target - entry
    risk_reward = reward / risk if risk > 0 else 0

    if risk_reward < MIN_RISK_REWARD:
        return None

    return {
        "entry": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "primary_target": round(primary_target, 2),
        "risk": round(risk, 2),
        "reward": round(reward, 2),
        "risk_reward": round(risk_reward, 2),
    }
