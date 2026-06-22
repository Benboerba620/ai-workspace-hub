#!/usr/bin/env python3
"""Small OpenAI-compatible LLM client for pod2wiki.

The public project keeps provider details in environment variables instead of
hard-coded local endpoints. It supports one generic LLM_* block plus common
provider-specific variable names.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


class LLMError(RuntimeError):
    """Raised when provider configuration or API calls fail."""


PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {
        "key": "DEEPSEEK_API_KEY",
        "base": "DEEPSEEK_BASE_URL",
        "model": "DEEPSEEK_MODEL",
        "base_default": "https://api.deepseek.com/v1",
        "model_default": "deepseek-chat",
    },
    "kimi": {
        "key": "KIMI_API_KEY",
        "base": "KIMI_BASE_URL",
        "model": "KIMI_MODEL",
        "base_default": "https://api.moonshot.cn/v1",
        "model_default": "moonshot-v1-128k",
    },
    "glm": {
        "key": "GLM_API_KEY",
        "base": "GLM_BASE_URL",
        "model": "GLM_MODEL",
        "base_default": "https://open.bigmodel.cn/api/paas/v4",
        "model_default": "glm-4-flash",
    },
    "qwen": {
        "key": "DASHSCOPE_API_KEY",
        "base": "QWEN_BASE_URL",
        "model": "QWEN_MODEL",
        "base_default": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_default": "qwen-plus",
    },
    "openai": {
        "key": "OPENAI_API_KEY",
        "base": "OPENAI_BASE_URL",
        "model": "OPENAI_MODEL",
        "base_default": "https://api.openai.com/v1",
        "model_default": "gpt-4o-mini",
    },
}

PLACEHOLDER_VALUES = {
    "",
    "sk-xxx",
    "xxx.xxx",
    "your_api_key_here",
    "your_deepseek_api_key_here",
    "your_kimi_api_key_here",
    "your_glm_api_key_here",
    "your_qwen_api_key_here",
    "your_openai_api_key_here",
}


def env_value(name: str) -> str | None:
    """Return a real env value, ignoring documented placeholders."""
    value = os.environ.get(name)
    if value is None:
        return None
    cleaned = value.strip().strip("\"'")
    if cleaned.lower() in PLACEHOLDER_VALUES:
        return None
    return cleaned


def load_dotenv(path: Path | None = None) -> None:
    """Load a simple .env file without adding a dependency."""
    candidates = []
    if path:
        candidates.append(path)
    candidates.extend([Path.cwd() / ".env", Path(__file__).resolve().parents[1] / ".env"])
    for candidate in candidates:
        if not candidate.is_file():
            continue
        for raw in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def resolve_provider(provider: str | None = None, model: str | None = None) -> dict[str, str]:
    """Resolve provider config from env vars."""
    load_dotenv()
    name = provider or env_value("LLM_PROVIDER") or "deepseek"
    if name not in PROVIDERS:
        raise LLMError(f"Unknown provider: {name}. Valid providers: {', '.join(PROVIDERS)}")
    cfg = PROVIDERS[name]
    api_key = env_value("LLM_API_KEY") or env_value(cfg["key"])
    if not api_key:
        raise LLMError(
            "Missing API key. Set LLM_API_KEY or the provider-specific key from .env.example."
        )
    return {
        "provider": name,
        "api_key": api_key,
        "base_url": env_value("LLM_BASE_URL") or env_value(cfg["base"]) or cfg["base_default"],
        "model": model or env_value("LLM_MODEL") or env_value(cfg["model"]) or cfg["model_default"],
    }


def chat(
    messages: list[dict[str, str]],
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.2,
    timeout: int = 120,
) -> str:
    """Call an OpenAI-compatible chat/completions endpoint and return text."""
    resolved = resolve_provider(provider, model)
    base = resolved["base_url"].rstrip("/")
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {resolved['api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": resolved["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise LLMError(f"LLM request failed: {exc}") from exc
    if response.status_code >= 400:
        raise LLMError(f"LLM request failed: HTTP {response.status_code} {response.text[:500]}")
    data: dict[str, Any] = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected LLM response: {json.dumps(data)[:500]}") from exc


def extract_json(text: str) -> dict[str, Any]:
    """Parse strict or code-fenced JSON returned by a model."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise
