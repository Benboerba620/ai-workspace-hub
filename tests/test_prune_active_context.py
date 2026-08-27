from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

from _test_paths import REPO_ROOT  # noqa: F401


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRUNE = load_module(
    "prune_active_context", REPO_ROOT / "system/scripts/prune_active_context.py"
)

TODAY = date(2026, 3, 20)


def build_workspace(tmp: Path, entries: str) -> Path:
    """Create a minimal workspace root with an active-context.md."""
    (tmp / "workspace" / "meta").mkdir(parents=True)
    (tmp / "workspace" / "workspace-config.md").write_text("# config\n", encoding="utf-8")
    active = tmp / "workspace" / "meta" / "active-context.md"
    active.write_text(
        "# Active Context\n\n## 最近对话延续\n\n"
        + entries
        + "\n## 当前关注\n\n- 这一段脚本不许碰\n",
        encoding="utf-8",
    )
    return active


def run(active: Path, **kwargs) -> dict:
    lines = active.read_text(encoding="utf-8").split("\n")
    result = PRUNE.plan(
        lines,
        kwargs.get("today", TODAY),
        kwargs.get("cutoff_days", 14),
        kwargs.get("max_entries", 20),
        kwargs.get("line_cap", 1500),
    )
    assert result is not None
    PRUNE.apply_plan(
        active,
        active.parent,
        lines,
        result,
        kwargs.get("cutoff_days", 14),
        kwargs.get("line_cap", 1500),
    )
    return result


class PruneActiveContextTest(unittest.TestCase):
    def test_archives_entries_older_than_cutoff(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            active = build_workspace(
                tmp,
                "- **2026-01-05：很久以前的事（DONE）** -> `output/a.md` 摘要\n"
                "- **2026-03-19：昨天的事（PAUSED）** -> `output/b.md` 摘要\n",
            )
            run(active)
            body = active.read_text(encoding="utf-8")
            self.assertNotIn("很久以前的事", body)
            self.assertIn("昨天的事", body)
            archive = tmp / "workspace/meta/active-context-archive-2026-01.md"
            self.assertIn("很久以前的事", archive.read_text(encoding="utf-8"))

    def test_keeps_other_sections_untouched(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            active = build_workspace(
                tmp, "- **2026-01-05：老条目（DONE）** -> `output/a.md` 摘要\n"
            )
            run(active)
            self.assertIn("这一段脚本不许碰", active.read_text(encoding="utf-8"))

    def test_entry_count_cap_archives_oldest(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            entries = "".join(
                f"- **2026-03-{day:02d}：第 {day} 条（DONE）** -> `output/{day}.md` 摘要\n"
                for day in range(8, 20)
            )
            active = build_workspace(tmp, entries)
            result = run(active, max_entries=5)
            self.assertEqual(len(result["to_keep"]), 5)
            self.assertEqual(result["over_count"], 7)
            body = active.read_text(encoding="utf-8")
            self.assertNotIn("第 8 条", body)
            self.assertIn("第 19 条", body)

    def test_line_cap_compresses_long_entry_and_keeps_full_text(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            long_body = "  详细正文，" * 400  # 远超 1500 字节
            active = build_workspace(
                tmp,
                "- **2026-03-18：超长条目（PAUSED）** -> `output/long.md` 摘要\n"
                f"{long_body}\n",
            )
            run(active)
            body = active.read_text(encoding="utf-8")
            self.assertIn("超长条目", body)
            self.assertNotIn("详细正文", body)
            self.assertIn("📦 全文见", body)
            self.assertIn("`output/long.md`", body)
            index_line = next(ln for ln in body.split("\n") if "超长条目" in ln)
            self.assertLessEqual(len(index_line.encode("utf-8")), 1500)
            archive = tmp / "workspace/meta/active-context-archive-2026-03.md"
            self.assertIn("详细正文", archive.read_text(encoding="utf-8"))

    def test_line_cap_zero_disables_compression(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            long_body = "  详细正文，" * 400
            active = build_workspace(
                tmp,
                "- **2026-03-18：超长条目（PAUSED）** -> `output/long.md` 摘要\n"
                f"{long_body}\n",
            )
            result = run(active, line_cap=0)
            self.assertEqual(result["to_compress"], [])
            self.assertIn("详细正文", active.read_text(encoding="utf-8"))

    def test_idempotent_on_rerun(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            active = build_workspace(
                tmp,
                "- **2026-01-05：老条目（DONE）** -> `output/a.md` 摘要\n"
                "- **2026-03-18：超长条目（PAUSED）** -> `output/long.md` 摘要\n"
                + "  详细正文，" * 400
                + "\n",
            )
            run(active)
            first_jan = (tmp / "workspace/meta/active-context-archive-2026-01.md").read_text(
                encoding="utf-8"
            )
            first_mar = (tmp / "workspace/meta/active-context-archive-2026-03.md").read_text(
                encoding="utf-8"
            )
            run(active)
            run(active)
            self.assertEqual(
                first_jan,
                (tmp / "workspace/meta/active-context-archive-2026-01.md").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertEqual(
                first_mar,
                (tmp / "workspace/meta/active-context-archive-2026-03.md").read_text(
                    encoding="utf-8"
                ),
            )

    def test_missing_section_returns_none(self):
        lines = "# Active Context\n\n## 别的段\n\n- 内容\n".split("\n")
        self.assertIsNone(PRUNE.plan(lines, TODAY, 14, 20, 1500))


if __name__ == "__main__":
    unittest.main()
