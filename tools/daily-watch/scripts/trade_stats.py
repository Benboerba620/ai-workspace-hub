"""
统计 portfolio/trades.csv 中的交易概况。

Usage:
  python scripts/trade_stats.py
  python scripts/trade_stats.py --hypothesis H1
  python scripts/trade_stats.py --ticker AAPL
  python scripts/trade_stats.py --month 2026-04
  python scripts/trade_stats.py --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from workspace_paths import find_workspace_root, resolve_trades_path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_trades(trades_path: Path) -> list[dict[str, str]]:
    if not trades_path.exists():
        return []
    with trades_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def filter_trades(
    trades: list[dict[str, str]],
    hypothesis: str | None = None,
    ticker: str | None = None,
    month: str | None = None,
) -> list[dict[str, str]]:
    result = trades
    if hypothesis:
        hypothesis_tag = f"[{hypothesis}]"
        result = [
            trade
            for trade in result
            if hypothesis_tag
            in (trade.get("reasoning", "") + trade.get("kill_thesis", ""))
        ]
    if ticker:
        result = [
            trade
            for trade in result
            if trade.get("ticker", "").upper() == ticker.upper()
        ]
    if month:
        result = [trade for trade in result if trade.get("date", "").startswith(month)]
    return result


def compute_stats(trades: list[dict[str, str]]) -> dict[str, object]:
    if not trades:
        return {"total": 0, "buys": 0, "sells": 0, "adds": 0, "reduces": 0, "closes": 0}

    action_counts: defaultdict[str, int] = defaultdict(int)
    tickers: set[str] = set()
    for trade in trades:
        action = trade.get("action", "").upper()
        action_counts[action] += 1
        if trade.get("ticker"):
            tickers.add(trade["ticker"])

    return {
        "total": len(trades),
        "buys": action_counts.get("BUY", 0),
        "sells": action_counts.get("SELL", 0),
        "adds": action_counts.get("ADD", 0),
        "reduces": action_counts.get("REDUCE", 0),
        "closes": action_counts.get("CLOSE", 0),
        "unique_tickers": len(tickers),
        "tickers": sorted(tickers),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Trade statistics")
    parser.add_argument("--hypothesis", help="Filter by hypothesis tag, e.g. H1")
    parser.add_argument("--ticker", help="Filter by ticker")
    parser.add_argument("--month", help="Filter by month, e.g. 2026-04")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    workspace_root = find_workspace_root(Path(__file__).resolve().parent)
    trades_path = resolve_trades_path(workspace_root)
    trades = load_trades(trades_path)
    filtered = filter_trades(trades, args.hypothesis, args.ticker, args.month)
    stats = compute_stats(filtered)

    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    if stats["total"] == 0:
        print("No matching trades found.")
        return 0

    label = ""
    if args.hypothesis:
        label += f" [{args.hypothesis}]"
    if args.ticker:
        label += f" [{args.ticker}]"
    if args.month:
        label += f" [{args.month}]"

    print(f"Trade statistics{label}:\n")
    print(f"  Total trades: {stats['total']}")
    print(
        f"  Buy: {stats['buys']}  Add: {stats['adds']}  "
        f"Sell: {stats['sells']}  Reduce: {stats['reduces']}  "
        f"Close: {stats['closes']}"
    )
    tickers = ", ".join(stats.get("tickers", []))
    print(f"  Tickers: {stats['unique_tickers']} ({tickers})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
