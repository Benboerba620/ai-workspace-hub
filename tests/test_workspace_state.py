from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from _test_paths import REPO_ROOT  # noqa: F401
from generate_daily_report import apply_hypothesis_updates  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATUS = load_module(
    "workspace_status", REPO_ROOT / "system/scripts/workspace_status.py"
)
UPGRADE = load_module(
    "upgrade_workspace", REPO_ROOT / "system/scripts/upgrade_workspace.py"
)
QUEUE = load_module(
    "review_queue", REPO_ROOT / "system/scripts/review_queue.py"
)


class EvidenceLedgerTests(unittest.TestCase):
    def test_daily_signal_creates_evidence_and_links_hypothesis_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hypothesis_dir = root / "hypothesis"
            report = root / "daily-watchlist-reports/2026-07/2026-07-11.md"
            hypothesis_dir.mkdir(parents=True)
            report.parent.mkdir(parents=True)
            report.write_text("# report\n", encoding="utf-8")
            hypothesis_path = hypothesis_dir / "H1-theme.md"
            hypothesis_path.write_text(
                "---\nid: H1\ncertainty: 50\nstatus: active\n---\n\n"
                "# H1: Theme\n\n## 证据时间线\n",
                encoding="utf-8",
            )
            hypotheses = [{"id": "H1", "path": hypothesis_path}]
            signals = [
                {
                    "hypothesis_id": "H1",
                    "hypothesis_title": "Theme",
                    "signal_type": "mover",
                    "ref": "IFX.DE",
                    "summary": "IFX.DE 今日涨跌幅 3.2%",
                    "auto_writeback": True,
                }
            ]

            self.assertEqual(
                apply_hypothesis_updates(
                    root, hypotheses, signals, report, "2026-07-11"
                ),
                1,
            )
            self.assertEqual(
                apply_hypothesis_updates(
                    root, hypotheses, signals, report, "2026-07-11"
                ),
                0,
            )
            evidence_files = list((root / "evidence/2026-07").glob("E-*.md"))
            self.assertEqual(len(evidence_files), 1)
            evidence = evidence_files[0].read_text(encoding="utf-8")
            self.assertIn("review_status: pending", evidence)
            self.assertIn("linked_hypotheses:\n- H1", evidence)
            hypothesis = hypothesis_path.read_text(encoding="utf-8")
            self.assertEqual(
                hypothesis.count("DW-2026-07-11-mover-ifx-de-h1"), 1
            )


class WorkspaceStatusTests(unittest.TestCase):
    def test_status_surfaces_pending_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace/workspace-config.md").write_text(
                "# config\n", encoding="utf-8"
            )
            (root / "workspace/research-profile.md").write_text(
                "- version: `v0.1`\n- calibrated_research_count: `1`\n",
                encoding="utf-8",
            )
            (root / "workspace/review-queue.md").write_text(
                "| ID | 类型 | 对象 | 建议动作 | 来源 | 创建日期 | 状态 |\n"
                "|---|---|---|---|---|---|---|\n"
                "| Q1 | hypothesis | H1 | review | R1 | 2026-07-11 | pending |\n",
                encoding="utf-8",
            )
            evidence = root / "evidence/2026-07/E1.md"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                "---\nid: E1\ntype: evidence\nreview_status: pending\n---\n",
                encoding="utf-8",
            )
            research = root / "output/research/r1.md"
            research.parent.mkdir(parents=True)
            research.write_text(
                "---\nid: R1\nstatus: active\n---\n", encoding="utf-8"
            )

            status = STATUS.collect_status(root)
            self.assertEqual(len(status["active_research"]), 1)
            self.assertEqual(len(status["pending_evidence"]), 1)
            self.assertEqual(len(status["pending_reviews"]), 1)
            self.assertFalse(status["watchlist_ready"])


class ReviewQueueTests(unittest.TestCase):
    def test_queue_add_is_idempotent_and_status_can_be_updated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workspace/review-queue.md"
            item, created = QUEUE.add_item(
                path,
                item_type="hypothesis",
                object_id="H1",
                action="复盘 | 确定性",
                source="E1",
                today=date(2026, 7, 11),
            )
            duplicate, duplicate_created = QUEUE.add_item(
                path,
                item_type="hypothesis",
                object_id="H1",
                action="复盘 | 确定性",
                source="E1",
                today=date(2026, 7, 11),
            )
            self.assertTrue(created)
            self.assertFalse(duplicate_created)
            self.assertEqual(item["id"], "Q-20260711-01")
            self.assertEqual(duplicate["id"], item["id"])
            self.assertTrue(QUEUE.update_item(path, item["id"], "done"))
            rows = QUEUE.parse_rows(path.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "done")
            self.assertEqual(rows[0]["action"], "复盘 / 确定性")


class UpgradeWorkspaceTests(unittest.TestCase):
    def test_upgrade_applies_only_managed_files_and_keeps_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            target = base / "target"
            (source / "system").mkdir(parents=True)
            (target / "system").mkdir(parents=True)
            (target / "wiki").mkdir()
            (source / "system/tool.md").write_text("new", encoding="utf-8")
            (source / "system/.ruff_cache").mkdir()
            (source / "system/.ruff_cache/cache.bin").write_text("cache")
            (source / "system/.env.local").write_text("SECRET=leak")
            (target / "system/tool.md").write_text("old", encoding="utf-8")
            (target / "wiki/user.md").write_text("keep", encoding="utf-8")
            manifest = {
                "hub_version": "9.9.9",
                "ownership": {
                    "managed": ["system/**"],
                    "user_owned": ["wiki/**"],
                    "mixed": [],
                },
            }
            (source / "system/managed-files.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            changes = UPGRADE.compare(source, target, manifest)
            managed_paths = {item["path"] for item in changes["managed"]}
            self.assertNotIn("system/.ruff_cache/cache.bin", managed_paths)
            self.assertNotIn("system/.env.local", managed_paths)
            applied, backup = UPGRADE.apply_managed(
                source, target, manifest, changes
            )
            self.assertGreaterEqual(applied, 1)
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertEqual(
                (backup / "system/tool.md").read_text(encoding="utf-8"), "old"
            )
            self.assertEqual(
                (target / "system/tool.md").read_text(encoding="utf-8"), "new"
            )
            self.assertEqual((target / "wiki/user.md").read_text(), "keep")

    def test_additive_migration_creates_missing_file_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            target = base / "target"
            (source / "system/templates").mkdir(parents=True)
            target.mkdir()
            (source / "system/templates/queue.md").write_text(
                "empty queue", encoding="utf-8"
            )
            manifest = {
                "hub_version": "9.9.9",
                "ownership": {"managed": [], "user_owned": [], "mixed": []},
                "migrations": {
                    "additive_directories": ["evidence"],
                    "additive_files": [
                        {
                            "source": "system/templates/queue.md",
                            "target": "workspace/review-queue.md",
                        }
                    ],
                },
            }
            changes = UPGRADE.compare(source, target, manifest)
            applied, _ = UPGRADE.apply_managed(source, target, manifest, changes)
            self.assertEqual(applied, 2)
            self.assertTrue((target / "evidence").is_dir())
            queue = target / "workspace/review-queue.md"
            self.assertEqual(queue.read_text(encoding="utf-8"), "empty queue")

            queue.write_text("user content", encoding="utf-8")
            changes = UPGRADE.compare(source, target, manifest)
            UPGRADE.apply_managed(source, target, manifest, changes)
            self.assertEqual(queue.read_text(encoding="utf-8"), "user content")


if __name__ == "__main__":
    unittest.main()
