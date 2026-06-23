from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PODCAST_SCRIPTS = REPO_ROOT / "tools" / "podcast" / "scripts"
sys.path.insert(0, str(PODCAST_SCRIPTS))

from llm_client import resolve_provider  # noqa: E402


class LLMConfigTests(unittest.TestCase):
    def test_environment_overrides_example_yaml_provider_and_model(self) -> None:
        env = {
            "LLM_API_KEY": "test-key",
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": "https://example.invalid/v1",
            "LLM_MODEL": "workspace-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = resolve_provider(provider="deepseek", model="deepseek-v4-flash")
        self.assertEqual(config["provider"], "openai")
        self.assertEqual(config["model"], "workspace-model")
        self.assertEqual(config["base_url"], "https://example.invalid/v1")


if __name__ == "__main__":
    unittest.main()
