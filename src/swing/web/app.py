"""FastAPI web application for the swing trading dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from swing.analysis.indicators import compute_indicators
from swing.analysis.levels import compute_levels
from swing.analysis.scorer import compute_score, rank_candidates
from swing.analysis.signals import detect_signals
from swing.data.cache import (
    clear_old_cache,
    get_cached_results,
    save_scan_results,
)
from swing.data.fetcher import fetch_ohlcv
from swing.config import MIN_PRICE, MIN_PRICE_US, WARMUP_DAYS
from swing.data.nifty_indices import (
    get_nifty100_stocks,
    get_nifty200_stocks,
    get_nifty50_stocks,
    get_nifty500_stocks,
)
from swing.data.us_stocks import get_dow30_stocks, get_nasdaq100_stocks, get_sp500_stocks
from swing.utils.logger import get_logger

log = get_logger(__name__)

app = FastAPI(title="Swing Trading Screener", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the dashboard."""
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api/results")
async def results(market: str = "nifty_500", scope: int = 500):
    """Return cached scan results for today, or null if none exist."""
    cache_key = f"{market}_{scope}"
    cached = get_cached_results(cache_key)
    if cached:
        return JSONResponse(cached)
    return JSONResponse({"cached": False})


@app.get("/api/scan")
async def scan(market: str = "nifty_500", max_stocks: int | None = None):
    """Run the screener and return JSON results. Caches results for the day."""
    scope = max_stocks if max_stocks else 500

    # Check cache first (per market)
    cache_key = f"{market}_{scope}"
    cached = get_cached_results(cache_key)
    if cached:
        return JSONResponse(cached)

    market_fetchers = {
        "nifty_50": get_nifty50_stocks,
        "nifty_100": get_nifty100_stocks,
        "nifty_200": get_nifty200_stocks,
        "nifty_500": get_nifty500_stocks,
        "dow_30": get_dow30_stocks,
        "nasdaq_100": get_nasdaq100_stocks,
        "sp_500": get_sp500_stocks,
    }
    
    us_markets = {"dow_30", "nasdaq_100", "sp_500"}

    fetcher = market_fetchers.get(market)
    if not fetcher:
        return JSONResponse({"error": f"Unknown market: {market}"}, status_code=400)

    # No cache — run fresh scan
    stocks = fetcher()
    if not stocks:
        return JSONResponse({"error": f"Could not load stock list for {market}"}, status_code=500)

    if max_stocks:
        stocks = stocks[:max_stocks]

    clear_old_cache()

    candidates = []
    stats = {"total": len(stocks), "scanned": 0, "filtered": 0, "skipped": 0}

    for stock_info in stocks:
        ticker = stock_info["yf_ticker"]
        symbol = stock_info["symbol"]

        df = fetch_ohlcv(ticker)
        if df is None or len(df) < WARMUP_DAYS:
            stats["skipped"] += 1
            stats["scanned"] += 1
            continue

        df = compute_indicators(df)
        min_price = MIN_PRICE_US if market in us_markets else MIN_PRICE
        result = detect_signals(df, min_price=min_price)

        if not result.get("passed"):
            stats["filtered"] += 1
            stats["scanned"] += 1
            continue

        levels = compute_levels(result)
        if levels is None:
            stats["filtered"] += 1
            stats["scanned"] += 1
            continue

        score_result = compute_score(result, levels)

        # Get sparkline data (last 30 closes)
        sparkline = df["Close"].tail(30).tolist()

        candidates.append(
            {
                "symbol": symbol,
                "company": stock_info["company"],
                "industry": stock_info["industry"],
                "score": score_result["total"],
                "score_breakdown": score_result["factors"],
                "signals": result["signals"],
                "signal_count": result["signal_count"],
                "latest": result["latest"],
                "levels": levels,
                "sparkline": [round(v, 2) for v in sparkline],
            }
        )
        stats["scanned"] += 1

    candidates = rank_candidates(candidates)

    # Build response and cache it
    response_data = {
        "candidates": candidates,
        "stats": stats,
        "count": len(candidates),
        "market": market,
    }

    scanned_at = save_scan_results(cache_key, response_data)
    response_data["scanned_at"] = scanned_at
    response_data["cached"] = False

    return JSONResponse(response_data)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


def start_server():
    """Start the uvicorn server."""
    import uvicorn
    from swing.config import WEB_HOST, WEB_PORT

    print(f"\n🌐 Dashboard starting at http://localhost:{WEB_PORT}\n")
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT, log_level="info")
