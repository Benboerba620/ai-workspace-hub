from __future__ import annotations

import importlib.util
import io
import tempfile
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from _test_paths import REPO_ROOT  # noqa: F401
from generate_daily_report import (  # noqa: E402
    apply_hypothesis_updates,
    read_hypotheses,
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INSTALLER = load_module(
    "e2e_install_workspace", REPO_ROOT / "system/scripts/install_workspace.py"
)
CHECKER = load_module(
    "e2e_check_workspace", REPO_ROOT / "system/scripts/check_workspace.py"
)
STATUS = load_module(
    "e2e_workspace_status", REPO_ROOT / "system/scripts/workspace_status.py"
)
QUEUE = load_module(
    "e2e_review_queue", REPO_ROOT / "system/scripts/review_queue.py"
)
PREFLIGHT = load_module(
    "e2e_research_preflight", REPO_ROOT / "system/scripts/research_preflight.py"
)


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert old in content
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def test_fresh_stock_research_reaches_reviewed_evidence_loop() -> None:
    """Fresh install -> research -> hypothesis -> daily evidence -> review."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "workspace"
        INSTALLER.install(
            REPO_ROOT,
            root,
            merge=False,
            name="E2E_STOCK_RESEARCH",
            primary_use="investing",
            wiki_root="./wiki",
        )
        with redirect_stdout(io.StringIO()):
            assert CHECKER.check(root) == 0

        today = date(2026, 7, 11)
        research_path = root / "output/research/2026-07-11-infineon.md"
        research_path.write_text(
            "---\n"
            "id: R20260711-01\n"
            "type: research\n"
            "title: Infineon research\n"
            "date: 2026-07-11\n"
            "status: active\n"
            "mode: 收敛\n"
            "linked_hypotheses: [H1]\n"
            "linked_entities: [IFX.DE]\n"
            "preflight_id:\n"
            "knowledge_used: []\n"
            "wiki_pages_loaded: []\n"
            "---\n\n"
            "# Infineon research\n\n"
            "## 核心结论\n\n"
            "[推测] AI 电源架构升级可能扩大高压功率器件需求。\n",
            encoding="utf-8",
        )
        preflight = PREFLIGHT.build_preflight(
            root,
            context="Infineon IFX.DE AI power architecture",
            research_id="R20260711-01",
            tickers=["IFX.DE"],
        )
        PREFLIGHT.update_research_file(root, research_path, preflight)
        PREFLIGHT.save_receipt(root, preflight)
        PREFLIGHT.lifecycle.record_load(
            root, preflight["context"], preflight["knowledge"], "R20260711-01"
        )

        hypothesis_path = root / "hypothesis/H1-ai-power-architecture.md"
        hypothesis_path.write_text(
            "---\n"
            "id: H1\n"
            "type: hypothesis\n"
            "certainty: 50\n"
            "status: active\n"
            "created: 2026-07-11\n"
            "updated_at: 2026-07-11\n"
            "last_reviewed_at:\n"
            "next_review_at: 2026-07-12\n"
            "scope: theme\n"
            "linked_research: [R20260711-01]\n"
            "linked_entities: [IFX.DE]\n"
            "---\n\n"
            "# H1: AI 电源架构升级提升高压功率器件价值量\n\n"
            "## 证据时间线\n",
            encoding="utf-8",
        )

        watchlist = root / "config/daily-watchlist-watchlist.md"
        watchlist.write_text(
            "| Ticker | Name | Market | Market Cap | Category | Tier | Hypothesis | Notes |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| IFX.DE | Infineon | EU | Large | Semiconductor | HOT | H1 | Power devices |\n",
            encoding="utf-8",
        )

        report_path = root / "output/daily-watch/2026-07/2026-07-11.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# 每日监控简报 - 2026-07-11\n", encoding="utf-8")
        hypotheses = read_hypotheses(root)
        assert hypotheses[0]["id"] == "H1"
        assert hypotheses[0]["tickers"] == {"IFX.DE"}
        signal = {
            "hypothesis_id": "H1",
            "hypothesis_title": "AI power architecture",
            "signal_type": "mover",
            "ref": "IFX.DE",
            "summary": "IFX.DE 当日价格变动达到日报阈值",
            "auto_writeback": True,
        }
        assert (
            apply_hypothesis_updates(
                root, hypotheses, [signal], report_path, today.isoformat()
            )
            == 1
        )

        queue_item, created = QUEUE.add_item(
            root / "workspace/review-queue.md",
            item_type="hypothesis",
            object_id="H1",
            action="复盘新增证据，不因价格本身调整确定性",
            source="E-2026-07-11-mover-ifx-de-h1",
            today=today,
        )
        assert created

        before_review = STATUS.collect_status(root)
        assert len(before_review["active_research"]) == 1
        assert len(before_review["open_hypotheses"]) == 1
        assert len(before_review["pending_evidence"]) == 1
        assert len(before_review["pending_reviews"]) == 1
        assert before_review["watchlist_ready"] is True

        evidence_path = next((root / "evidence/2026-07").glob("E-*.md"))
        replace_once(evidence_path, "review_status: pending", "review_status: confirmed")
        replace_once(evidence_path, "direction: pending", "direction: neutral")
        replace_once(research_path, "status: active", "status: closed")
        replace_once(hypothesis_path, "last_reviewed_at:\n", "last_reviewed_at: 2026-07-11\n")
        assert QUEUE.update_item(
            root / "workspace/review-queue.md", queue_item["id"], "done"
        )

        after_review = STATUS.collect_status(root)
        assert after_review["active_research"] == []
        assert after_review["pending_evidence"] == []
        assert after_review["pending_reviews"] == []
        assert len(after_review["open_hypotheses"]) == 1
        assert "E-2026-07-11-mover-ifx-de-h1" in hypothesis_path.read_text(
            encoding="utf-8"
        )
