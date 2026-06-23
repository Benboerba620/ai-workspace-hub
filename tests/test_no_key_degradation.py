from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class NoKeyDegradationTests(unittest.TestCase):
    def test_macro_fetcher_returns_empty_payload_without_fmp_key(self) -> None:
        env = os.environ.copy()
        env.pop("FMP_API_KEY", None)
        completed = subprocess.run(
            [sys.executable, "tools/daily-watch/scripts/fetch_macro_data.py"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["macro"], {})
        self.assertEqual(payload["sentiment"], "Unknown")
        self.assertEqual(payload["meta"]["reason"], "FMP_API_KEY not set")


if __name__ == "__main__":
    unittest.main()
