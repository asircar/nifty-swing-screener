"""CLI entry point for the swing trading screener."""

from __future__ import annotations

import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from swing.analysis.indicators import compute_indicators
from swing.analysis.levels import compute_levels
from swing.analysis.scorer import compute_score, rank_candidates
from swing.analysis.signals import detect_signals
from swing.data.cache import clear_old_cache
from swing.data.fetcher import fetch_ohlcv
from swing.config import MIN_PRICE, MIN_PRICE_US
from swing.data.nifty_indices import (
    get_nifty100_stocks,
    get_nifty200_stocks,
    get_nifty50_stocks,
    get_nifty500_stocks,
)
from swing.data.us_stocks import get_dow30_stocks, get_nasdaq100_stocks, get_sp500_stocks
from swing.utils.logger import get_logger

log = get_logger(__name__)
console = Console()


def _signal_icons(signals: dict) -> str:
    """Render signal flags as colored icons."""
    icons = {
        "ema_aligned": ("📈", "EMA"),
        "rsi_recovery": ("📊", "RSI"),
        "macd_crossover": ("🔀", "MACD"),
        "support_bounce": ("🔄", "SUP"),
        "volume_surge": ("📢", "VOL"),
    }
    parts = []
    for key, (icon, label) in icons.items():
        if signals.get(key):
            parts.append(f"{icon}{label}")
    return " ".join(parts)


def run_screener(market: str = "nifty_500", max_stocks: int | None = None) -> list[dict]:
    """Run the full screener pipeline and return ranked candidates."""
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
        console.print(f"[red]❌ Unknown market: {market}[/]")
        console.print(f"[dim]Available: {', '.join(market_fetchers.keys())}[/]")
        return []

    console.print(
        Panel(
            f"[bold cyan]🔍 Swing Trading Screener — {market}[/]\n"
            "[dim]Scanning for swing trade opportunities...[/]",
            border_style="cyan",
        )
    )

    # Step 1: Get stock list
    console.print(f"\n[bold yellow]Step 1:[/] Fetching {market} stock list...")
    stocks = fetcher()
    if not stocks:
        console.print("[red]❌ Could not load stock list. Exiting.[/]")
        return []
    console.print(f"  [green]✓[/] Loaded [bold]{len(stocks)}[/] stocks\n")

    if max_stocks:
        stocks = stocks[:max_stocks]

    # Step 2: Clear old cache
    clear_old_cache()

    # Step 3: Scan each stock
    console.print("[bold yellow]Step 2:[/] Scanning stocks (downloading + analyzing)...\n")
    candidates: list[dict] = []
    skipped = 0
    filtered = 0

    with Progress(
        TextColumn("[bold blue]{task.fields[ticker]}"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning...", total=len(stocks), ticker="")

        for stock_info in stocks:
            ticker = stock_info["yf_ticker"]
            symbol = stock_info["symbol"]
            progress.update(task, ticker=symbol)

            # Fetch data
            df = fetch_ohlcv(ticker)
            if df is None or len(df) < 50:
                skipped += 1
                progress.advance(task)
                continue

            # Compute indicators
            df = compute_indicators(df)

            # Detect signals
            min_price = MIN_PRICE_US if market in us_markets else MIN_PRICE
            result = detect_signals(df, min_price=min_price)

            if not result.get("passed"):
                if result.get("reason") == "filter_failed":
                    filtered += 1
                else:
                    skipped += 1
                progress.advance(task)
                continue

            # Compute levels
            levels = compute_levels(result)
            if levels is None:
                filtered += 1
                progress.advance(task)
                continue

            # Score
            score_result = compute_score(result, levels)

            # Build candidate
            candidates.append(
                {
                    "symbol": symbol,
                    "company": stock_info["company"],
                    "industry": stock_info["industry"],
                    "ticker": ticker,
                    "score": score_result["total"],
                    "score_breakdown": score_result["factors"],
                    "signals": result["signals"],
                    "signal_count": result["signal_count"],
                    "latest": result["latest"],
                    "levels": levels,
                    "supports": result.get("supports", []),
                    "resistances": result.get("resistances", []),
                }
            )

            progress.advance(task)

    # Step 4: Rank
    candidates = rank_candidates(candidates)

    console.print(
        f"\n  [green]✓[/] Scan complete: "
        f"[bold green]{len(candidates)}[/] candidates found, "
        f"{filtered} filtered, {skipped} skipped\n"
    )

    return candidates


def display_results(candidates: list[dict]) -> None:
    """Display results in a rich table."""
    if not candidates:
        console.print(
            Panel("[yellow]No swing trade candidates found today.[/]", border_style="yellow")
        )
        return

    table = Table(
        title="🎯 Swing Trade Candidates",
        title_style="bold green",
        border_style="bright_blue",
        show_lines=True,
        pad_edge=True,
    )

    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Symbol", style="bold cyan", width=12)
    table.add_column("Company", width=20, overflow="ellipsis")
    table.add_column("Score", justify="center", width=7)
    table.add_column("CMP (₹)", justify="right", width=10)
    table.add_column("Entry (₹)", justify="right", width=10)
    table.add_column("Stop Loss (₹)", justify="right", width=12)
    table.add_column("Target (₹)", justify="right", width=10)
    table.add_column("R:R", justify="center", width=5)
    table.add_column("Signals", width=24)
    table.add_column("RSI", justify="center", width=6)

    for i, c in enumerate(candidates, 1):
        lvl = c["levels"]
        latest = c["latest"]

        # Color score
        score = c["score"]
        if score >= 70:
            score_str = f"[bold green]{score}[/]"
        elif score >= 50:
            score_str = f"[yellow]{score}[/]"
        else:
            score_str = f"[dim]{score}[/]"

        # Color R:R
        rr = lvl["risk_reward"]
        if rr >= 3:
            rr_str = f"[bold green]{rr}[/]"
        else:
            rr_str = f"[green]{rr}[/]"

        rsi_val = latest.get("rsi")
        rsi_str = f"{rsi_val:.0f}" if rsi_val else "—"

        table.add_row(
            str(i),
            c["symbol"],
            c["company"][:20],
            score_str,
            f"{latest['close']:.2f}",
            f"{lvl['entry']:.2f}",
            f"[red]{lvl['stop_loss']:.2f}[/]",
            f"[green]{lvl['primary_target']:.2f}[/]",
            rr_str,
            _signal_icons(c["signals"]),
            rsi_str,
        )

    console.print(table)

    # Legend
    console.print(
        "\n[dim]Signals: 📈 EMA Aligned  │  📊 RSI Recovery  │  "
        "🔀 MACD Crossover  │  🔄 Support Bounce  │  📢 Volume Surge[/]"
    )
    console.print(
        "[dim]CMP = Current Market Price  │  R:R = Risk:Reward Ratio  │  "
        "Min R:R = 2.0[/]\n"
    )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Swing Trading Screener — Multi-Market",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-m", "--market",
        type=str,
        default="nifty_500",
        help="Market to scan: nifty_50, nifty_100, nifty_200, nifty_500, dow_30, nasdaq_100, sp_500",
    )
    parser.add_argument(
        "-n", "--max-stocks",
        type=int,
        default=None,
        help="Limit scan to first N stocks (for testing)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch web dashboard instead of CLI output",
    )
    args = parser.parse_args()

    if args.web:
        from swing.web.app import start_server
        start_server()
        return

    start = time.time()
    candidates = run_screener(market=args.market, max_stocks=args.max_stocks)
    display_results(candidates)
    elapsed = time.time() - start
    console.print(f"[dim]Completed in {elapsed:.1f}s[/]")


if __name__ == "__main__":
    main()
