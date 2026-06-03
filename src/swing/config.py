"""Configuration constants for the swing trading screener."""

from pathlib import Path

# ──────────────────────────── Paths ────────────────────────────
# Fallback CSVs are bundled inside the package so they're available
# both in development (editable install) and on deployed servers
# (regular pip install where __file__ resolves to site-packages).
_PKG_DATA = Path(__file__).resolve().parent / "data"

# Writable cache lives in /tmp so it works on read-only deployed filesystems.
_CACHE_DIR = Path("/tmp") / "swing"

DB_PATH = _CACHE_DIR / "cache.db"
FALLBACK_CSV = _PKG_DATA / "nifty500_fallback.csv"
NIFTY50_FALLBACK_CSV = _PKG_DATA / "nifty50_fallback.csv"
NIFTY100_FALLBACK_CSV = _PKG_DATA / "nifty100_fallback.csv"
NIFTY200_FALLBACK_CSV = _PKG_DATA / "nifty200_fallback.csv"
SP500_FALLBACK_CSV = _PKG_DATA / "sp500_fallback.csv"
DOW30_FALLBACK_CSV = _PKG_DATA / "dow30_fallback.csv"
NASDAQ100_FALLBACK_CSV = _PKG_DATA / "nasdaq100_fallback.csv"

# ──────────────────────────── Data ─────────────────────────────
NIFTY50_CSV_URL = (
    "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
)
NIFTY100_CSV_URL = (
    "https://archives.nseindia.com/content/indices/ind_nifty100list.csv"
)
NIFTY200_CSV_URL = (
    "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
)
NIFTY500_CSV_URL = (
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
)
HISTORY_PERIOD = "1y"          # download 1 year of daily data
WARMUP_DAYS = 220              # enough for 200-day EMA warm-up

# ──────────────────────────── Indicators ───────────────────────
EMA_SHORT = 20
EMA_MID = 50
EMA_LONG = 200
RSI_PERIOD = 14
RSI_OVERSOLD = 40
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14
VOLUME_SMA_PERIOD = 20

# ──────────────────────────── Signal Thresholds ────────────────
MIN_SIGNALS_REQUIRED = 2       # at least N primary signals to qualify
SUPPORT_PROXIMITY_PCT = 0.02   # price within 2% of support
VOLUME_SURGE_FACTOR = 1.5      # volume ≥ 1.5× average

# ──────────────────────────── Filters ──────────────────────────
MIN_PRICE = 50.0               # ₹50 minimum (India)
MIN_PRICE_US = 5.0             # $5 minimum (US)
MIN_AVG_VOLUME = 100_000       # 100K shares/day

# ──────────────────────────── Levels ───────────────────────────
ATR_SL_MULTIPLIER = 1.5        # stop loss = entry − 1.5 × ATR
MIN_RISK_REWARD = 2.0          # minimum risk:reward ratio

# ──────────────────────────── Scoring Weights ──────────────────
SCORE_WEIGHTS = {
    "signals": 0.30,
    "risk_reward": 0.25,
    "volume": 0.15,
    "trend": 0.15,
    "rsi": 0.15,
}

# ──────────────────────────── Web ──────────────────────────────
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000
