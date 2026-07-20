#!/usr/bin/env python3
"""Compatibility import for the Hub-wide LLM client."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system.lib.llm_client import (  # noqa: E402,F401
    LLMError,
    PLACEHOLDER_VALUES,
    PROVIDERS,
    chat,
    env_value,
    extract_json,
    load_dotenv,
    resolve_provider,
)

__all__ = [
    "LLMError",
    "PLACEHOLDER_VALUES",
    "PROVIDERS",
    "chat",
    "env_value",
    "extract_json",
    "load_dotenv",
    "resolve_provider",
]
