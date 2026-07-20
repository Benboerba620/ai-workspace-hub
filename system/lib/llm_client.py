#!/usr/bin/env python3
"""Small shared client for OpenAI-compatible chat completion APIs."""

from __future__ import annotations

import json
import os
import time
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
        "model_default": "deepseek-v4-flash",
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

TRANSIENT_MARKERS = (
    "connection",
    "timeout",
    "timed out",
    "429",
    "500",
    "502",
    "503",
    "504",
    "reset",
)


def env_value(name: str) -> str | None:
    """Return a real environment value while ignoring documented placeholders."""
    value = os.environ.get(name)
    if value is None:
        return None
    cleaned = value.strip().strip("\"'")
    if cleaned.lower() in PLACEHOLDER_VALUES:
        return None
    return cleaned


def _workspace_root(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    return None


def load_dotenv(path: Path | None = None) -> None:
    """Load workspace LLM settings without overriding existing environment values."""
    protected_keys = set(os.environ)
    candidates: list[Path] = []
    if path:
        candidates.append(path)
    root = _workspace_root(Path.cwd()) or _workspace_root(Path(__file__))
    candidates.append(Path.cwd() / ".env")
    if root:
        candidates.extend(
            [
                root / "config" / "pod2wiki.env",
                root / ".env",
                root / "tools" / "podcast" / ".env",
            ]
        )

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate in seen or not candidate.is_file():
            continue
        seen.add(candidate)
        for raw in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key in protected_keys:
                continue
            current = os.environ.get(key)
            if current is None or current.strip().strip("\"'").lower() in PLACEHOLDER_VALUES:
                os.environ[key] = value


def resolve_provider(
    provider: str | None = None, model: str | None = None
) -> dict[str, str]:
    """Resolve provider configuration with explicit args taking precedence."""
    load_dotenv()
    env_provider = env_value("LLM_PROVIDER")
    name = provider or env_provider or "deepseek"
    if name not in PROVIDERS:
        raise LLMError(f"Unknown provider: {name}. Valid providers: {', '.join(PROVIDERS)}")
    cfg = PROVIDERS[name]
    generic_ok = env_provider is None or env_provider == name
    api_key = (env_value("LLM_API_KEY") if generic_ok else None) or env_value(cfg["key"])
    if not api_key:
        raise LLMError(
            "Missing API key. Set LLM_API_KEY or a provider-specific API key."
        )
    base_url = (
        (env_value("LLM_BASE_URL") if generic_ok else None)
        or env_value(cfg["base"])
        or cfg["base_default"]
    )
    resolved_model = (
        model
        or (env_value("LLM_MODEL") if generic_ok else None)
        or env_value(cfg["model"])
        or cfg["model_default"]
    )
    return {
        "provider": name,
        "api_key": api_key,
        "base_url": base_url,
        "model": resolved_model,
    }


def _is_transient(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in TRANSIENT_MARKERS)


def chat(
    messages: list[dict[str, str]],
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.2,
    timeout: int = 120,
    *,
    json_mode: bool = False,
    max_attempts: int = 3,
) -> str:
    """Call an OpenAI-compatible endpoint and return the assistant text."""
    resolved = resolve_provider(provider, model)
    base = resolved["base_url"].rstrip("/")
    payload: dict[str, Any] = {
        "model": resolved["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    last_error: LLMError | None = None
    for attempt in range(max(1, max_attempts)):
        session = requests.Session()
        session.trust_env = False
        try:
            response = session.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {resolved['api_key']}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
            if response.status_code >= 400:
                raise LLMError(
                    f"LLM request failed: HTTP {response.status_code} {response.text[:500]}"
                )
            data: dict[str, Any] = response.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise LLMError(
                    f"Unexpected LLM response: {json.dumps(data)[:500]}"
                ) from exc
        except requests.RequestException as exc:
            last_error = LLMError(f"LLM request failed: {exc}")
        except (LLMError, ValueError) as exc:
            last_error = exc if isinstance(exc, LLMError) else LLMError(str(exc))

        if last_error and _is_transient(str(last_error)) and attempt < max_attempts - 1:
            time.sleep(2**attempt)
            continue
        break
    raise last_error or LLMError("LLM request failed without an error message")


def _ensure_json_object(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise LLMError(f"Expected a JSON object from the model, got {type(data).__name__}")
    return data


def extract_json(text: str) -> dict[str, Any]:
    """Parse a strict or code-fenced JSON object returned by a model."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return _ensure_json_object(json.loads(cleaned))
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return _ensure_json_object(json.loads(cleaned[start : end + 1]))
        raise
