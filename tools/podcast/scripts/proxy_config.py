#!/usr/bin/env python3
"""Proxy helpers.

Set PODCAST_PROXY to a full proxy URL such as socks5://127.0.0.1:1080.
If it is missing, the tools run direct instead of failing.
"""
from __future__ import annotations

import os
import socket


def _port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def detect_proxy() -> str | None:
    explicit = os.environ.get("PODCAST_PROXY")
    if explicit:
        return explicit
    for port in range(12345, 12351):
        if _port_open("127.0.0.1", port):
            return f"socks5://127.0.0.1:{port}"
    return None


PROXY = detect_proxy()
CURL_PROXY = PROXY


def requests_proxy() -> dict[str, str] | None:
    if not PROXY:
        return None
    return {"http": PROXY, "https": PROXY}
