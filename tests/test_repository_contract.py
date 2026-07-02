from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_entrypoint_templates_match_public_entrypoints(self) -> None:
        pairs = (
            ("system/templates/AGENTS.md", "AGENTS.md"),
            ("system/templates/CLAUDE.md", "CLAUDE.md"),
            ("system/templates/workspace-config.md", "workspace/workspace-config.md"),
            ("system/templates/active-context.md", "workspace/meta/active-context.md"),
            ("system/templates/friction-log.md", "workspace/meta/friction-log.md"),
        )
        for template, public in pairs:
            self.assertEqual(
                (REPO_ROOT / template).read_text(encoding="utf-8"),
                (REPO_ROOT / public).read_text(encoding="utf-8"),
                f"{template} and {public} diverged",
            )

    def test_all_relative_markdown_links_resolve(self) -> None:
        pattern = re.compile(r"\[[^]]*\]\(([^)]+)\)")
        broken: list[str] = []
        for markdown in REPO_ROOT.rglob("*.md"):
            if ".git" in markdown.parts:
                continue
            for target in pattern.findall(markdown.read_text(encoding="utf-8")):
                target = target.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                path = (markdown.parent / target.replace("%20", " ")).resolve()
                if not path.exists():
                    broken.append(f"{markdown.relative_to(REPO_ROOT)} -> {target}")
        self.assertEqual(broken, [])

    def test_longbridge_is_not_claimed_as_builtin_env_provider(self) -> None:
        market_script = (
            REPO_ROOT / "tools/daily-watch/scripts/fetch_market_data.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("LONGBRIDGE_APP_KEY", market_script)
        self.assertNotIn("fetch_longbridge", market_script)

    def test_optional_transcription_is_not_in_base_requirements(self) -> None:
        requirements = (
            REPO_ROOT / "tools/podcast/requirements.txt"
        ).read_text(encoding="utf-8")
        active = [
            line.strip()
            for line in requirements.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertFalse(any(line.startswith("faster-whisper") for line in active))
        self.assertTrue(
            (REPO_ROOT / "tools/podcast/requirements-transcribe.txt").is_file()
        )
        self.assertTrue(
            (REPO_ROOT / "tools/daily-watch/requirements-tushare.txt").is_file()
        )

    def test_example_secrets_are_treated_as_unconfigured(self) -> None:
        market_script = (
            REPO_ROOT / "tools/daily-watch/scripts/fetch_market_data.py"
        ).read_text(encoding="utf-8")
        macro_script = (
            REPO_ROOT / "tools/daily-watch/scripts/fetch_macro_data.py"
        ).read_text(encoding="utf-8")
        self.assertIn('startswith("your_")', market_script)
        self.assertIn('startswith("your_")', macro_script)


if __name__ == "__main__":
    unittest.main()
