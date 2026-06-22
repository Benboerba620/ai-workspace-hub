#!/usr/bin/env python3
"""
Daily Watchlist - Macro Data Fetcher
Fetches macro market indicators: VIX, major indices, commodities, crypto.

Data source: FMP (Financial Modeling Prep)

Usage:
    python fetch_macro_data.py

Output: JSON to stdout. Logs to stderr.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import dotenv_values
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv", file=sys.stderr)
    sys.exit(1)

from workspace_paths import find_workspace_root, resolve_config_dir, resolve_env_path


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

ROOT = find_workspace_root(Path(__file__).resolve().parent)
CONFIG_DIR = resolve_config_dir(ROOT)
ENV_PATH = resolve_env_path(CONFIG_DIR)


def load_env_file(env_path: Path) -> None:
    if not env_path.is_file():
        return
    raw_text = env_path.read_text(encoding="utf-8-sig")
    parsed = dotenv_values(stream=StringIO(raw_text))
    for key, value in parsed.items():
        if value is not None and key not in os.environ:
            os.environ[key] = value


load_env_file(ENV_PATH)

FMP_API_KEY = os.getenv("FMP_API_KEY", "")
FMP_BASE = "https://financialmodelingprep.com/api/v3"

MACRO_TICKERS = {
    "indices": ["SPY", "QQQ", "IWM"],
    "commodities": ["GLD", "USO", "CLUSD", "BZUSD"],
    "crypto": ["BTCUSD"],
    "volatility": ["VIXY"],
}
VIX_SYMBOL = "^VIX"
VIX_ENDPOINT = "quote/%5EVIX"


def fmp_get(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    if not FMP_API_KEY:
        print("ERROR: FMP_API_KEY not set", file=sys.stderr)
        return None
    url = f"{FMP_BASE}/{endpoint}"
    request_params = {"apikey": FMP_API_KEY}
    if params:
        request_params.update(params)
    try:
        response = requests.get(url, params=request_params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001
        print(f"FMP error ({endpoint}): {exc}", file=sys.stderr)
        return None


def vix_status(vix_value: float | None) -> str:
    if vix_value is None:
        return "Unknown"
    if vix_value < 15:
        return "Optimistic"
    if vix_value < 20:
        return "Normal"
    if vix_value < 30:
        return "Cautious"
    return "Panic"


def build_quote_payload(quote: dict[str, Any] | None, *, label: str | None = None) -> dict[str, Any]:
    payload = {
        "price": None,
        "change_pct": None,
        "change": None,
    }
    if label is not None:
        payload["label"] = label
    if quote:
        payload["price"] = quote.get("price")
        payload["change_pct"] = quote.get("changesPercentage")
        payload["change"] = quote.get("change")
    return payload


def main() -> None:
    configure_stdio()

    if not FMP_API_KEY:
        print(f"ERROR: FMP_API_KEY not set in {ENV_PATH}", file=sys.stderr)
        json.dump({"error": "FMP_API_KEY not set"}, sys.stdout)
        sys.exit(1)

    result = {
        "macro": {},
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "missing_symbols": [],
        },
    }

    print("Fetching VIX...", file=sys.stderr)
    vix_data = fmp_get(VIX_ENDPOINT)
    vix_quote = vix_data[0] if isinstance(vix_data, list) and vix_data else None
    vix_price = vix_quote.get("price") if vix_quote else None
    result["macro"]["VIX"] = {
        "price": vix_price,
        "change": vix_quote.get("change") if vix_quote else None,
        "change_pct": vix_quote.get("changesPercentage") if vix_quote else None,
        "status": vix_status(vix_price),
    }
    if not vix_quote:
        result["meta"]["missing_symbols"].append(VIX_SYMBOL)

    all_tickers: list[str] = []
    for group in MACRO_TICKERS.values():
        all_tickers.extend(group)

    print(f"Fetching {len(all_tickers)} macro tickers...", file=sys.stderr)
    joined = ",".join(all_tickers)
    quotes = fmp_get(f"quote/{joined}") or []
    quote_map = {
        quote["symbol"]: quote
        for quote in quotes
        if isinstance(quote, dict) and "symbol" in quote
    }

    for ticker in MACRO_TICKERS["indices"]:
        result["macro"][ticker] = build_quote_payload(quote_map.get(ticker))
        if ticker not in quote_map:
            result["meta"]["missing_symbols"].append(ticker)

    commodity_labels = {
        "GLD": "Gold",
        "USO": "Oil ETF",
        "CLUSD": "WTI Crude",
        "BZUSD": "Brent Crude",
    }
    for ticker in MACRO_TICKERS["commodities"]:
        result["macro"][ticker] = build_quote_payload(
            quote_map.get(ticker),
            label=commodity_labels.get(ticker, ticker),
        )
        if ticker not in quote_map:
            result["meta"]["missing_symbols"].append(ticker)

    wti = quote_map.get("CLUSD", {}).get("price")
    brent = quote_map.get("BZUSD", {}).get("price")
    result["macro"]["BW_spread"] = (
        round(brent - wti, 2)
        if isinstance(wti, (int, float)) and isinstance(brent, (int, float))
        else None
    )

    btc = quote_map.get("BTCUSD")
    result["macro"]["BTC"] = build_quote_payload(btc)
    result["macro"]["BTC"].pop("change", None)
    if "BTCUSD" not in quote_map:
        result["meta"]["missing_symbols"].append("BTCUSD")

    vixy = quote_map.get("VIXY")
    result["macro"]["VIXY"] = build_quote_payload(vixy)
    result["macro"]["VIXY"].pop("change", None)
    if "VIXY" not in quote_map:
        result["meta"]["missing_symbols"].append("VIXY")

    vix_val = result["macro"]["VIX"]["price"]
    spy_change = result["macro"]["SPY"]["change_pct"]
    sentiment = vix_status(vix_val)
    if sentiment != "Unknown" and isinstance(spy_change, (int, float)):
        if spy_change > 1:
            sentiment += ", risk-on"
        elif spy_change < -1:
            sentiment += ", risk-off"

    result["sentiment"] = sentiment
    result["meta"]["requested_symbols"] = len(all_tickers) + 1
    result["meta"]["received_symbols"] = len(quote_map) + (1 if vix_quote else 0)
    result["meta"]["missing_symbols"] = sorted(set(result["meta"]["missing_symbols"]))

    print(
        f"Macro data fetched: {result['meta']['received_symbols']}/{result['meta']['requested_symbols']} symbols",
        file=sys.stderr,
    )
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
