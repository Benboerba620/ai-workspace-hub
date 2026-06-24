from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _test_paths import REPO_ROOT  # noqa: F401 (also sets up sys.path)

from check_setup import initialize_config  # noqa: E402
from fetch_market_data import fetch_nasdaq_quote, load_env  # noqa: E402
from workspace_paths import find_workspace_root  # noqa: E402


class WorkspacePathTests(unittest.TestCase):
    def test_integrated_workspace_is_found_before_config_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "workspace-config.md").write_text(
                "# Workspace Config\n", encoding="utf-8"
            )
            script_dir = root / "tools" / "daily-watch" / "scripts"
            script_dir.mkdir(parents=True)
            self.assertEqual(find_workspace_root(script_dir), root.resolve())

    def test_standalone_workspace_falls_back_to_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "daily-watchlist.yaml").write_text(
                "modules: {}\n", encoding="utf-8"
            )
            script_dir = root / "scripts"
            script_dir.mkdir()
            self.assertEqual(find_workspace_root(script_dir), root.resolve())

    def test_initialize_config_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = initialize_config(root)
            second = initialize_config(root)
            self.assertEqual(len(first), 5)
            self.assertEqual(second, [])
            self.assertTrue((root / "config" / "daily-watchlist.yaml").is_file())

    def test_placeholder_api_keys_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "daily-watchlist.env"
            env_file.write_text(
                "FMP_API_KEY=your_fmp_api_key\nTUSHARE_TOKEN=your_tushare_token\n",
                encoding="utf-8",
            )
            with patch.dict("os.environ", {}, clear=True):
                values = load_env(env_file)
            self.assertEqual(values["FMP_API_KEY"], "")
            self.assertEqual(values["TUSHARE_TOKEN"], "")

    @patch("fetch_market_data.requests.get")
    def test_nasdaq_fallback_normalizes_quote(self, mock_get) -> None:
        response = mock_get.return_value
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "data": {
                "primaryData": {
                    "lastSalePrice": "$297.01",
                    "netChange": "-1.00",
                    "percentageChange": "-0.34%",
                    "lastTradeTimestamp": "Jun 22, 2026",
                    "volume": "44,880,180",
                }
            }
        }
        quote = fetch_nasdaq_quote("AAPL", "US")
        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote["price"], 297.01)
        self.assertEqual(quote["changesPercentage"], -0.34)
        self.assertEqual(quote["volume"], 44880180.0)
        self.assertEqual(quote["source"], "nasdaq")


if __name__ == "__main__":
    unittest.main()
