from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "system" / "scripts" / "install_workspace.py"
CHECKER_PATH = REPO_ROOT / "system" / "scripts" / "check_workspace.py"
DOCTOR_PATH = REPO_ROOT / "system" / "scripts" / "workspace_doctor.py"
SPEC = importlib.util.spec_from_file_location("install_workspace", INSTALLER_PATH)
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)
CHECKER_SPEC = importlib.util.spec_from_file_location("check_workspace", CHECKER_PATH)
assert CHECKER_SPEC and CHECKER_SPEC.loader
CHECKER = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(CHECKER)
DOCTOR_SPEC = importlib.util.spec_from_file_location("workspace_doctor", DOCTOR_PATH)
assert DOCTOR_SPEC and DOCTOR_SPEC.loader
DOCTOR = importlib.util.module_from_spec(DOCTOR_SPEC)
DOCTOR_SPEC.loader.exec_module(DOCTOR)


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
            self.assertTrue((target / "workspace/cache").is_dir())
            self.assertTrue((target / "workspace/monitoring").is_dir())
            self.assertTrue((target / "workspace/archive").is_dir())
            self.assertTrue((target / "output/daily-watch").is_dir())
            required = (
                "AGENTS.md",
                "CLAUDE.md",
                "START-HERE.md",
                "workspace/workspace-config.md",
                "workspace/research-profile.md",
                "workspace/review-queue.md",
                "evidence/README.md",
                "wiki/_schema.md",
                "wiki/explorations/_index.md",
                "wiki/explorations/_template.md",
                "wiki/patterns/_index.md",
                "wiki/patterns/_template.md",
                "wiki/rules/_index.md",
                "wiki/rules/_template.md",
                "wiki/rules.md",
                "wiki/false-beliefs.md",
                "config/daily-watchlist.yaml",
                "config/daily-watchlist.env",
                "config/pod2wiki.config.yaml",
                "requirements.lock",
                "tools/daily-watch/scripts/check_setup.py",
                "tools/podcast/scripts/fetch_podcasts.py",
                "system/scripts/pdf_to_md.py",
                "system/scripts/check_workspace.py",
                "system/scripts/wiki_tagger.py",
                "system/scripts/knowledge_lifecycle.py",
                "system/scripts/research_preflight.py",
                "system/scripts/workspace_status.py",
                "system/scripts/review_queue.py",
                "system/scripts/upgrade_workspace.py",
                "system/managed-files.json",
                "system/lib/llm_client.py",
                "system/skills/first-research.md",
                "system/skills/research-closeout.md",
                "system/skills/hypothesis-review.md",
                "system/skills/knowledge-lifecycle.md",
                "system/integrations/object-model.md",
                "workspace/.hub-state.json",
            )
            for relative in required:
                self.assertTrue((target / relative).is_file(), relative)
            config = (target / "workspace/workspace-config.md").read_text(encoding="utf-8")
            self.assertIn("name: `SANDBOX`", config)
            self.assertIn("primary_use: `investing`", config)
            watchlist = (target / "config/daily-watchlist-watchlist.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("唯一执行股票池", watchlist)
            self.assertNotIn("| AAPL |", watchlist)
            doctor = DOCTOR.validate(target)
            self.assertEqual(doctor["errors"], 0, doctor["findings"])
            state = json.loads(
                (target / "workspace/.hub-state.json").read_text(encoding="utf-8")
            )
            manifest = json.loads(
                (target / "system/managed-files.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["installed_version"], manifest["hub_version"])
            self.assertEqual(state["install_mode"], "fresh")
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
            state = json.loads(
                (target / "workspace/.hub-state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["install_mode"], "merge")


class ObsidianReadingHubTests(unittest.TestCase):
    def test_dashboard_base_is_valid_and_has_expected_views(self) -> None:
        base_path = REPO_ROOT / "system/templates/reading-hub.base"
        raw = base_path.read_bytes()
        dashboard = yaml.safe_load(raw)
        expected_views = {
            "🎯 今日看什么",
            "📥 Inbox（未读）",
            "🔬 研究",
            "🔍 筛选",
            "🎙️ Podcast",
            "📊 日报监控",
            "📚 Sources（近30天未读）",
            "⭐ 精读清单",
            "✅ 最近已读",
        }

        self.assertFalse(
            raw.startswith(b"\xef\xbb\xbf"),
            "Base template should not contain a BOM",
        )
        self.assertEqual({view["name"] for view in dashboard["views"]}, expected_views)

    def test_opt_in_installs_dashboard_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "workspace"
            INSTALLER.install(
                REPO_ROOT,
                target,
                merge=False,
                name="SANDBOX",
                primary_use="investing",
                wiki_root="./wiki",
                obsidian_reading_hub=True,
            )
            self.assertTrue((target / "reading-hub.base").is_file())
            self.assertTrue((target / "reading-hub.md").is_file())

    def test_dashboard_files_off_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "workspace"
            INSTALLER.install(
                REPO_ROOT,
                target,
                merge=False,
                name="SANDBOX",
                primary_use="investing",
                wiki_root="./wiki",
            )
            self.assertFalse((target / "reading-hub.base").exists())
            self.assertFalse((target / "reading-hub.md").exists())

    def test_existing_obsidian_vault_auto_enables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / ".obsidian").mkdir()
            INSTALLER.install(
                REPO_ROOT,
                target,
                merge=True,
                name="SANDBOX",
                primary_use="investing",
                wiki_root="./wiki",
            )
            self.assertTrue((target / "reading-hub.base").is_file())
            self.assertTrue((target / "reading-hub.md").is_file())


if __name__ == "__main__":
    unittest.main()
