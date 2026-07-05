from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "system" / "scripts" / "install_workspace.py"
CHECKER_PATH = REPO_ROOT / "system" / "scripts" / "check_workspace.py"
SPEC = importlib.util.spec_from_file_location("install_workspace", INSTALLER_PATH)
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)
CHECKER_SPEC = importlib.util.spec_from_file_location("check_workspace", CHECKER_PATH)
assert CHECKER_SPEC and CHECKER_SPEC.loader
CHECKER = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(CHECKER)


class InstallWorkspaceTests(unittest.TestCase):
    def test_fresh_install_contains_runnable_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "workspace"
            created, skipped = INSTALLER.install(
                REPO_ROOT,
                target,
                merge=False,
                name="SANDBOX",
                primary_use="investing",
                wiki_root="./wiki",
            )
            self.assertGreater(created, 50)
            self.assertEqual(skipped, 0)
            required = (
                "AGENTS.md",
                "CLAUDE.md",
                "workspace/workspace-config.md",
                "wiki/_schema.md",
                "config/daily-watchlist.yaml",
                "config/daily-watchlist.env",
                "config/pod2wiki.config.yaml",
                "tools/daily-watch/scripts/check_setup.py",
                "tools/podcast/scripts/fetch_podcasts.py",
                "system/scripts/pdf_to_md.py",
                "system/scripts/check_workspace.py",
            )
            for relative in required:
                self.assertTrue((target / relative).is_file(), relative)
            config = (target / "workspace/workspace-config.md").read_text(encoding="utf-8")
            self.assertIn("name: `SANDBOX`", config)
            self.assertIn("primary_use: `investing`", config)
            leaked = [
                path.relative_to(target).as_posix()
                for path in target.rglob("*")
                if path.name in {"__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache", ".DS_Store"}
                or path.suffix in {".pyc", ".pyo"}
                or (path.name.startswith(".env") and path.name != ".env.example")
            ]
            self.assertEqual(leaked, [], "installer must not copy caches or local .env files")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(CHECKER.check(target), 0)

    def test_nonempty_target_requires_explicit_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            existing = target / "notes.md"
            existing.write_text("keep me", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                INSTALLER.install(
                    REPO_ROOT,
                    target,
                    merge=False,
                    name="TEST",
                    primary_use="mixed",
                    wiki_root="./wiki",
                )
            INSTALLER.install(
                REPO_ROOT,
                target,
                merge=True,
                name="TEST",
                primary_use="mixed",
                wiki_root="./wiki",
            )
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()
