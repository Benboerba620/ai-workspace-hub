#!/usr/bin/env python3
"""Registry of public podcast RSS feeds plus iTunes lookup fallback."""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET

import requests


UA = "pod2wiki/0.1 (+https://github.com/Benboerba620/pod2wiki)"
TIMEOUT = 20

CHANNELS = [
    {
        "name": "Dwarkesh Patel",
        "category": "ai",
        "rss_url": "https://www.dwarkesh.com/feed",
        "itunes_id": None,
    },
    {
        "name": "Lex Fridman",
        "category": "ai",
        "rss_url": "https://lexfridman.com/feed/podcast/",
        "itunes_id": 1434243584,
    },
    {
        "name": "Latent Space",
        "category": "ai",
        "rss_url": "https://api.substack.com/feed/podcast/1084089.rss",
        "itunes_id": None,
    },
    {
        "name": "All-In Podcast",
        "category": "ai",
        "rss_url": "https://rss.libsyn.com/shows/254861/destinations/1928300.xml",
        "itunes_id": 1502871393,
    },
    {
        "name": "a16z",
        "category": "ai",
        "rss_url": "https://feeds.simplecast.com/JGE3yC0V",
        "itunes_id": 842818711,
    },
    {
        "name": "Macro Voices",
        "category": "energy",
        "rss_url": "https://feeds.feedburner.com/MacroVoices",
        "itunes_id": 1079172742,
    },
    {
        "name": "Super-Spiked",
        "category": "energy",
        "rss_url": "https://api.substack.com/feed/podcast/567871.rss",
        "itunes_id": 1599740437,
    },
    {
        "name": "Columbia Energy Exchange",
        "category": "energy",
        "rss_url": "https://rss.libsyn.com/shows/76724/destinations/343325.xml",
        "itunes_id": 1081481629,
    },
]


def itunes_lookup(apple_id: int) -> str | None:
    try:
        response = requests.get(
            f"https://itunes.apple.com/lookup?id={apple_id}",
            timeout=TIMEOUT,
            headers={"User-Agent": UA},
        )
        if response.status_code != 200:
            return None
        results = response.json().get("results") or []
        if not results:
            return None
        return results[0].get("feedUrl")
    except Exception:
        return None


def get_feed_url(channel: dict) -> str | None:
    url = channel.get("rss_url")
    if url:
        try:
            response = requests.head(
                url,
                timeout=TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": UA},
            )
            if response.status_code < 400:
                return url
        except Exception:
            pass
    apple_id = channel.get("itunes_id")
    if apple_id:
        return itunes_lookup(int(apple_id))
    return None


def list_channels(category: str | None = None) -> list[dict]:
    if not category:
        return CHANNELS
    return [item for item in CHANNELS if item.get("category") == category]


def verify_all() -> list[dict]:
    results = []
    for channel in CHANNELS:
        url = get_feed_url(channel)
        status = "missing"
        title = ""
        if url:
            try:
                response = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
                response.raise_for_status()
                root = ET.fromstring(response.content)
                title = root.findtext("./channel/title") or ""
                status = "ok"
            except Exception as exc:
                status = f"error: {exc}"
        results.append({"name": channel["name"], "category": channel["category"], "url": url, "status": status, "title": title})
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["ai", "energy"])
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = verify_all() if args.verify else list_channels(args.category)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
