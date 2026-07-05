from __future__ import annotations

import unittest
from unittest.mock import patch

import _test_paths  # noqa: F401

from llm_client import resolve_provider  # noqa: E402


class LLMConfigTests(unittest.TestCase):
    """Precedence contract: explicit arguments > environment > defaults."""

    def test_explicit_provider_beats_environment(self) -> None:
        env = {
            "LLM_API_KEY": "generic-key",
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": "https://example.invalid/v1",
            "LLM_MODEL": "workspace-model",
            "KIMI_API_KEY": "kimi-key",
        }
        with patch.dict("os.environ", env, clear=True):
            config = resolve_provider(provider="kimi")
        self.assertEqual(config["provider"], "kimi")
        # Generic LLM_* values belong to the env-selected provider (openai)
        # and must not leak into an explicitly requested one.
        self.assertEqual(config["api_key"], "kimi-key")
        self.assertEqual(config["base_url"], "https://api.moonshot.cn/v1")
        self.assertEqual(config["model"], "moonshot-v1-128k")

    def test_environment_applies_when_no_explicit_provider(self) -> None:
        env = {
            "LLM_API_KEY": "generic-key",
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": "https://example.invalid/v1",
            "LLM_MODEL": "workspace-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = resolve_provider()
        self.assertEqual(config["provider"], "openai")
        self.assertEqual(config["api_key"], "generic-key")
        self.assertEqual(config["base_url"], "https://example.invalid/v1")
        self.assertEqual(config["model"], "workspace-model")

    def test_explicit_model_beats_environment_model(self) -> None:
        env = {
            "LLM_API_KEY": "generic-key",
            "LLM_PROVIDER": "deepseek",
            "LLM_MODEL": "env-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = resolve_provider(model="cli-model")
        self.assertEqual(config["provider"], "deepseek")
        self.assertEqual(config["model"], "cli-model")


if __name__ == "__main__":
    unittest.main()
