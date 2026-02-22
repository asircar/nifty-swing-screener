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
from swing.data.nifty500 import get_nifty500_stocks
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
async def results(scope: int = 500):
    """Return cached scan results for today, or null if none exist."""
    cached = get_cached_results(scope)
    if cached:
        return JSONResponse(cached)
    return JSONResponse({"cached": False})


@app.get("/api/scan")
async def scan(max_stocks: int = 500):
    """Run the screener and return JSON results. Caches results for the day."""
    scope = max_stocks

    # Check cache first
    cached = get_cached_results(scope)
    if cached:
        return JSONResponse(cached)

    # No cache — run fresh scan
    stocks = get_nifty500_stocks()
    if not stocks:
        return JSONResponse({"error": "Could not load stock list"}, status_code=500)

    if max_stocks:
        stocks = stocks[:max_stocks]

    clear_old_cache()

    candidates = []
    stats = {"total": len(stocks), "scanned": 0, "filtered": 0, "skipped": 0}

    for stock_info in stocks:
        ticker = stock_info["yf_ticker"]
        symbol = stock_info["symbol"]

        df = fetch_ohlcv(ticker)
        if df is None or len(df) < 50:
            stats["skipped"] += 1
            stats["scanned"] += 1
            continue

        df = compute_indicators(df)
        result = detect_signals(df)

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
    }

    scanned_at = save_scan_results(scope, response_data)
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
