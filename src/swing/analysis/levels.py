"""Calculate entry, target, and stop-loss levels."""

from __future__ import annotations

from swing.config import ATR_SL_MULTIPLIER, MIN_RISK_REWARD


def compute_levels(signal_result: dict) -> dict | None:
    """Compute entry, stop-loss, and target levels for a swing candidate.

    Takes the output from detect_signals() and returns levels,
    or None if risk-reward is insufficient.

    Returns dict with:
        - entry: float
        - stop_loss: float
        - target_1: float (2:1 RR)
        - target_2: float (nearest resistance)
        - risk: float (entry - stop_loss)
        - reward: float (target_1 - entry)
        - risk_reward: float
    """
    latest = signal_result.get("latest", {})
    supports = signal_result.get("supports", [])
    resistances = signal_result.get("resistances", [])

    close = latest.get("close")
    atr = latest.get("atr")

    if close is None or atr is None or atr <= 0:
        return None

    # ── Entry ──
    # Use close price, or snap to nearest support if very close
    entry = close
    for sup in reversed(supports):
        if sup < close and (close - sup) / sup <= 0.01:
            entry = sup
            break

    # ── Stop Loss ──
    # ATR-based: entry − 1.5 × ATR
    atr_stop = entry - ATR_SL_MULTIPLIER * atr

    # Cross-check with nearest support below entry
    support_below = [s for s in supports if s < entry * 0.99]
    if support_below:
        nearest_support = support_below[-1]
        # Use the tighter of ATR stop and just below support
        support_stop = nearest_support * 0.995  # slight buffer below support
        stop_loss = max(atr_stop, support_stop)  # tighter = higher
    else:
        stop_loss = atr_stop

    # ── Targets ──
    risk = entry - stop_loss
    if risk <= 0:
        return None

    # Target 1: 2:1 risk-reward
    target_1 = entry + MIN_RISK_REWARD * risk

    # Target 2: nearest resistance above entry
    resistance_above = [r for r in resistances if r > entry * 1.01]
    target_2 = resistance_above[0] if resistance_above else target_1 * 1.02

    # Use the better target (resistance if it gives ≥ 2:1 RR)
    if target_2 > target_1:
        primary_target = target_2
    else:
        primary_target = target_1

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
