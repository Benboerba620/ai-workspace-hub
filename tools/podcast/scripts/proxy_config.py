#!/usr/bin/env python3
"""Proxy helpers.

PODCAST_PROXY semantics:
- unset / empty / "none" (also "off", "false", "0"): run direct, no proxy.
- "auto": scan localhost ports 12345-12350 and use the first open one as a
  SOCKS5 proxy (opt-in convenience for local proxy clients).
- any other value: used as-is as an explicit proxy URL, e.g.
  socks5://127.0.0.1:1080 (requires the PySocks extra: pip install "requests[socks]").
"""
from __future__ import annotations

import os
import socket

_DISABLED_VALUES = {"", "none", "off", "false", "0"}


def _port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _scan_local_ports() -> str | None:
    for port in range(12345, 12351):
        if _port_open("127.0.0.1", port):
            return f"socks5://127.0.0.1:{port}"
    return None


def detect_proxy() -> str | None:
    value = (os.environ.get("PODCAST_PROXY") or "").strip()
    if value.lower() in _DISABLED_VALUES:
        return None
    if value.lower() == "auto":
        return _scan_local_ports()
    return value


PROXY = detect_proxy()
CURL_PROXY = PROXY


def requests_proxy() -> dict[str, str] | None:
    if not PROXY:
        return None
    return {"http": PROXY, "https": PROXY}
