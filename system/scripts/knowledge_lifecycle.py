#!/usr/bin/env python3
"""Manage, summarize, and selectively load reusable workspace knowledge."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # Core Mode remains dependency-free.
    yaml = None

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

TYPE_PATHS = {
    "exploration": ("wiki/explorations",),
    # workspace/patterns remains readable for workspaces created during the preview period.
    "pattern": ("wiki/patterns", "workspace/patterns"),
    "rule": ("wiki/rules",),
}
INDEX_PATHS = {
    "exploration": "wiki/explorations/_index.md",
    "pattern": "wiki/patterns/_index.md",
    "rule": "wiki/rules/_index.md",
}
ID_PREFIXES = {"exploration": "EXP-", "pattern": "PAT-", "rule": "RULE-"}
STATUSES = {
    "exploration": {
        "tentative",
        "validated",
        "weakened",
        "invalidated",
        "promoted",
        "archived",
    },
    "pattern": {"draft", "active", "weakened", "promoted", "retired", "archived"},
    "rule": {"candidate", "active", "weakened", "deprecated", "archived"},
}
DEFAULT_LOAD_STATUSES = {
    "exploration": {"tentative", "validated", "promoted"},
    "pattern": {"active", "promoted"},
    "rule": {"active"},
}
TRANSITIONS = {
    "exploration": {
        "tentative": {"validated", "invalidated", "archived"},
        "validated": {"weakened", "promoted", "archived"},
        "weakened": {"validated", "invalidated", "archived"},
        "invalidated": {"tentative", "archived"},
        "promoted": {"weakened", "archived"},
        "archived": {"tentative"},
    },
    "pattern": {
        "draft": {"active", "retired", "archived"},
        "active": {"weakened", "promoted", "retired", "archived"},
        "weakened": {"active", "retired", "archived"},
        "promoted": {"weakened", "retired", "archived"},
        "retired": {"draft", "archived"},
        "archived": {"draft"},
    },
    "rule": {
        "candidate": {"active", "archived"},
        "active": {"weakened", "deprecated", "archived"},
        "weakened": {"active", "deprecated", "archived"},
        "deprecated": {"candidate", "archived"},
        "archived": {"candidate"},
    },
}
LIST_FIELDS = (
    "domain",
    "ticker",
    "concepts",
    "tags",
    "recall_signals",
    "decision_scenarios",
)


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    return current


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def read_page(path: Path) -> tuple[dict[str, Any], str, str | None]:
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return {}, "", str(exc)
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.DOTALL)
    if not match:
        return {}, content, "missing frontmatter"
    raw = match.group(1)
    if yaml is not None:
        try:
            payload = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:
            return {}, content, f"invalid YAML: {exc}"
        if not isinstance(payload, dict):
            return {}, content, "frontmatter is not a mapping"
        return payload, content, None

    values: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        field = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if field:
            key = field.group(1)
            value = field.group(2).strip().strip('"\'')
            current_key = key if not value else None
            if value.startswith("[") and value.endswith("]"):
                values[key] = [
                    item.strip().strip('"\'')
                    for item in value[1:-1].split(",")
                    if item.strip()
                ]
            else:
                values[key] = value or None
            continue
        item = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if item and current_key:
            values.setdefault(current_key, [])
            if isinstance(values[current_key], list):
                values[current_key].append(item.group(1).strip('"\''))
    return values, content, None


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def iter_pages(root: Path, selected_types: set[str] | None = None) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    wanted = selected_types or set(TYPE_PATHS)
    for knowledge_type in TYPE_PATHS:
        if knowledge_type not in wanted:
            continue
        for folder in TYPE_PATHS[knowledge_type]:
            base = root / folder
            if not base.is_dir():
                continue
            for path in sorted(base.glob("*.md")):
                if path.name.startswith("_") or path.name.lower() == "readme.md":
                    continue
                meta, content, error = read_page(path)
                pages.append(
                    {
                        "type": knowledge_type,
                        "path": path,
                        "relative_path": relative(path, root),
                        "meta": meta,
                        "content": content,
                        "error": error,
                    }
                )
    return pages


def is_overdue(value: Any, today: date | None = None) -> bool:
    if not value:
        return False
    try:
        return date.fromisoformat(str(value)[:10]) < (today or date.today())
    except ValueError:
        return False


def promotion_candidate(page: dict[str, Any]) -> str | None:
    meta = page["meta"]
    knowledge_type = page["type"]
    status = str(meta.get("status") or "")
    if knowledge_type == "exploration" and status == "validated":
        return "可复盘是否提炼为 pattern"
    if (
        knowledge_type == "pattern"
        and status == "active"
        and as_int(meta.get("primary_confirmations")) >= 3
    ):
        return "已满足 rule 的案例数量门槛"
    if (
        knowledge_type == "rule"
        and status == "candidate"
        and as_int(meta.get("independent_confirmations")) >= 3
    ):
        return "可确认是否启用为 active rule"
    return None


def summarize(root: Path) -> dict[str, Any]:
    pages = iter_pages(root)
    counts: dict[str, dict[str, int]] = {}
    overdue: list[dict[str, str]] = []
    candidates: list[dict[str, str]] = []
    calls = Counter()
    for page in pages:
        knowledge_type = page["type"]
        status = str(page["meta"].get("status") or "missing")
        counts.setdefault(knowledge_type, {})[status] = (
            counts.setdefault(knowledge_type, {}).get(status, 0) + 1
        )
        item_id = str(page["meta"].get("id") or page["path"].stem)
        if is_overdue(page["meta"].get("review_due")):
            overdue.append({"id": item_id, "type": knowledge_type, "path": page["relative_path"]})
        candidate = promotion_candidate(page)
        if candidate:
            candidates.append(
                {"id": item_id, "type": knowledge_type, "reason": candidate, "path": page["relative_path"]}
            )

    usage_path = root / "workspace" / "knowledge-usage.jsonl"
    if usage_path.is_file():
        for line in usage_path.read_text(encoding="utf-8-sig").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "load":
                calls.update(str(item) for item in event.get("knowledge_ids", []))
    return {
        "counts": counts,
        "overdue": overdue,
        "promotion_candidates": candidates,
        "most_loaded": [{"id": key, "count": count} for key, count in calls.most_common(10)],
    }


def compact(value: Any, limit: int = 3) -> str:
    values = as_list(value)
    return "、".join(values[:limit]) + ("…" if len(values) > limit else "")


def markdown_link(page: dict[str, Any], index_path: str) -> str:
    index_parent = Path(index_path).parent
    target = Path(page["relative_path"])
    try:
        link = target.relative_to(index_parent)
    except ValueError:
        link = Path("../..") / target
    return str(link).replace("\\", "/")


def render_index(root: Path, knowledge_type: str) -> str:
    pages = iter_pages(root, {knowledge_type})
    index_path = INDEX_PATHS[knowledge_type]
    title = {"exploration": "Exploration", "pattern": "Pattern", "rule": "Rule"}[knowledge_type]
    intro = (
        f"> 自动生成的 {title} 路由摘要。先匹配召回信号和决策场景，再按链接加载全文；"
        "不要在本文件手工维护证据。\n"
    )
    headers = {
        "exploration": "| ID | Exploration | 状态 | 一句话结论 | 召回信号 | 复审 |\n|---|---|---|---|---|---|",
        "pattern": "| ID | Pattern | 状态 | 一句话结构 | 召回信号 | 失效信号 | 复审 |\n|---|---|---|---|---|---|---|",
        "rule": "| ID | Rule | 状态 | 适用范围 | 规则摘要 | 失效信号 | 复审 |\n|---|---|---|---|---|---|---|",
    }
    rows: list[str] = []
    for page in sorted(pages, key=lambda item: str(item["meta"].get("id") or item["path"].stem)):
        meta = page["meta"]
        item_id = str(meta.get("id") or page["path"].stem)
        name = str(meta.get("title") or page["path"].stem).replace("|", "/")
        linked = f"[{name}]({markdown_link(page, index_path)})"
        status = str(meta.get("status") or "missing")
        summary = str(meta.get("summary") or "").replace("|", "/")
        review_due = str(meta.get("review_due") or "-")
        if knowledge_type == "exploration":
            rows.append(
                f"| {item_id} | {linked} | {status} | {summary} | {compact(meta.get('recall_signals'))} | {review_due} |"
            )
        elif knowledge_type == "pattern":
            rows.append(
                f"| {item_id} | {linked} | {status} | {summary} | {compact(meta.get('recall_signals'))} | "
                f"{compact(meta.get('failure_signals'))} | {review_due} |"
            )
        else:
            rows.append(
                f"| {item_id} | {linked} | {status} | {str(meta.get('scope') or '').replace('|', '/')} | "
                f"{summary} | {compact(meta.get('invalidation_signals'))} | {review_due} |"
            )
    if not rows:
        rows.append("| - | 暂无条目 | - | - | - | - |" + ("" if knowledge_type == "exploration" else " - |"))
    return f"# {title} 索引\n\n{intro}\n{headers[knowledge_type]}\n" + "\n".join(rows) + "\n"


def rebuild_indexes(root: Path, apply: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for knowledge_type, relpath in INDEX_PATHS.items():
        path = root / relpath
        content = render_index(root, knowledge_type)
        old = path.read_text(encoding="utf-8-sig") if path.is_file() else None
        changed = old != content
        if apply and changed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        results.append({"type": knowledge_type, "path": relpath, "changed": changed, "applied": apply and changed})
    return results


def normalized(value: str) -> str:
    return re.sub(r"[\s_\-/]+", "", value.lower())


def field_matches(meta: dict[str, Any], field: str, wanted: list[str]) -> bool:
    if not wanted:
        return True
    actual = [normalized(item) for item in as_list(meta.get(field))]
    return any(
        normalized(query) == item or normalized(query) in item or item in normalized(query)
        for query in wanted
        for item in actual
        if item
    )


def score_page(page: dict[str, Any], context: str) -> tuple[int, list[str]]:
    meta = page["meta"]
    context_norm = normalized(context)
    score = 0
    reasons: list[str] = []
    weighted = (
        ("recall_signals", 8, "召回信号"),
        ("decision_scenarios", 6, "决策场景"),
        ("ticker", 6, "标的"),
        ("concepts", 4, "概念"),
        ("domain", 3, "领域"),
        ("tags", 2, "标签"),
    )
    for field, weight, label in weighted:
        hits = []
        for value in as_list(meta.get(field)):
            value_norm = normalized(value)
            if value_norm and (value_norm in context_norm or context_norm in value_norm):
                hits.append(value)
        if hits:
            score += weight * len(hits)
            reasons.append(f"{label}: {compact(hits, 2)}")
    title_summary = normalized(f"{meta.get('title') or ''} {meta.get('summary') or ''}")
    tokens = [token for token in re.split(r"[\s,，。；;:：/]+", context.lower()) if len(token) >= 2]
    weak_hits = [token for token in tokens if normalized(token) in title_summary][:3]
    if weak_hits:
        score += len(weak_hits)
        reasons.append("标题/摘要: " + "、".join(weak_hits))
    return score, reasons


def load_knowledge(
    root: Path,
    *,
    context: str,
    selected_types: set[str],
    limit: int,
    include_review: bool,
    all_active: bool,
    filters: dict[str, list[str]],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for page in iter_pages(root, selected_types):
        meta = page["meta"]
        status = str(meta.get("status") or "")
        if not include_review and status not in DEFAULT_LOAD_STATUSES[page["type"]]:
            continue
        if any(not field_matches(meta, field, wanted) for field, wanted in filters.items()):
            continue
        score, reasons = score_page(page, context) if context else (0, [])
        if not all_active and score <= 0 and not any(filters.values()):
            continue
        matches.append(
            {
                "id": str(meta.get("id") or page["path"].stem),
                "type": page["type"],
                "title": str(meta.get("title") or page["path"].stem),
                "status": status,
                "summary": str(meta.get("summary") or ""),
                "scope": str(meta.get("scope") or ""),
                "review_due": str(meta.get("review_due") or ""),
                "failure_signals": as_list(meta.get("failure_signals") or meta.get("invalidation_signals")),
                "path": page["relative_path"],
                "score": score,
                "matched_by": reasons or (["显式筛选"] if any(filters.values()) else ["全部生效知识"]),
                "content": page["content"],
            }
        )
    type_order = {"rule": 0, "pattern": 1, "exploration": 2}
    matches.sort(key=lambda item: (type_order[item["type"]], -item["score"], item["id"]))
    return matches[:limit]


def record_load(root: Path, context: str, matches: list[dict[str, Any]], research_id: str) -> str:
    now = datetime.now(timezone.utc)
    digest = hashlib.sha256(
        (now.isoformat() + context + "|".join(item["id"] for item in matches)).encode("utf-8")
    ).hexdigest()[:8]
    invocation_id = f"KU-{now.strftime('%Y%m%dT%H%M%SZ')}-{digest}"
    event = {
        "event": "load",
        "id": invocation_id,
        "at": now.isoformat(),
        "research_id": research_id or None,
        "context": context[:500],
        "knowledge_ids": [item["id"] for item in matches],
    }
    path = root / "workspace" / "knowledge-usage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return invocation_id


def transition_errors(page: dict[str, Any], target: str) -> list[str]:
    meta = page["meta"]
    knowledge_type = page["type"]
    current = str(meta.get("status") or "")
    errors: list[str] = []
    if target not in TRANSITIONS.get(knowledge_type, {}).get(current, set()):
        errors.append(f"不允许 {knowledge_type} 从 `{current}` 迁移到 `{target}`")
        return errors
    if target in {"validated", "active", "promoted"} and not meta.get("review_due"):
        errors.append("进入可调用或已晋级状态前必须设置 review_due")
    if knowledge_type == "exploration" and target == "validated" and len(as_list(meta.get("based_on"))) < 2:
        errors.append("exploration 至少关联两个独立来源才能 validated")
    if knowledge_type == "exploration" and target == "promoted" and not meta.get("promoted_to"):
        errors.append("exploration 晋级前必须填写 promoted_to")
    if knowledge_type == "pattern" and target == "active":
        if len(as_list(meta.get("source_explorations"))) < 2:
            errors.append("pattern 至少需要两个独立 exploration")
        if as_int(meta.get("primary_confirmations")) < 2:
            errors.append("pattern 至少需要两次 primary confirmation 才能 active")
    if knowledge_type == "pattern" and target == "promoted":
        if as_int(meta.get("primary_confirmations")) < 3:
            errors.append("pattern 至少需要三次 primary confirmation 才能晋级 rule")
        if not meta.get("promoted_to"):
            errors.append("pattern 晋级前必须填写 promoted_to")
    if knowledge_type == "rule" and target == "active":
        if not as_list(meta.get("source_patterns")):
            errors.append("rule 必须关联 source_patterns")
        if as_int(meta.get("independent_confirmations")) < 3:
            errors.append("rule 至少需要三个独立案例确认")
        if not meta.get("scope"):
            errors.append("rule 必须限定 scope")
        if not as_list(meta.get("invalidation_signals")):
            errors.append("rule 必须定义 invalidation_signals")
    return errors


def replace_frontmatter_scalar(content: str, field: str, value: str) -> str:
    match = re.match(r"^(---\s*\n)(.*?)(\n---\s*(?:\n|$))", content, re.DOTALL)
    if not match:
        raise ValueError("missing frontmatter")
    raw = match.group(2)
    line = f"{field}: {value}"
    pattern = re.compile(rf"(?m)^{re.escape(field)}:\s*.*$")
    raw = pattern.sub(line, raw, count=1) if pattern.search(raw) else raw.rstrip() + "\n" + line
    return match.group(1) + raw + match.group(3) + content[match.end() :]


def apply_transition(path: Path, target: str, reason: str, evidence: list[str]) -> None:
    meta, content, error = read_page(path)
    if error:
        raise ValueError(error)
    current = str(meta.get("status") or "")
    today = date.today().isoformat()
    content = replace_frontmatter_scalar(content, "status", target)
    content = replace_frontmatter_scalar(content, "updated_at", today)
    content = replace_frontmatter_scalar(content, "last_reviewed_at", today)
    details = f"- {today}: `{current}` -> `{target}`；原因：{reason.strip()}"
    if evidence:
        details += "；依据：" + "、".join(evidence)
    if "\n## 生命周期记录\n" in content:
        content = content.rstrip() + "\n" + details + "\n"
    else:
        content = content.rstrip() + "\n\n## 生命周期记录\n\n" + details + "\n"
    path.write_text(content, encoding="utf-8")


def queue_transition(
    root: Path,
    page: dict[str, Any],
    target: str,
    reason: str,
    evidence: list[str],
) -> tuple[dict[str, str], bool]:
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from review_queue import add_item, queue_path  # noqa: PLC0415

    source = str(page.get("relative_path") or page["path"].relative_to(root)).replace("\\", "/")
    if evidence:
        source += "；依据：" + "、".join(evidence)
    action = f"知识状态 {page['meta'].get('status')} -> {target}：{reason}"
    return add_item(
        queue_path(root),
        item_type=f"knowledge-{page['type']}",
        object_id=str(page["meta"].get("id") or page["path"].stem),
        action=action,
        source=source,
    )


def find_page(root: Path, requested: Path) -> dict[str, Any] | None:
    path = requested if requested.is_absolute() else root / requested
    resolved = path.resolve()
    for page in iter_pages(root):
        if page["path"].resolve() == resolved:
            return page
    return None


def render_load(matches: list[dict[str, Any]], full: bool) -> str:
    lines = [f"知识加载结果：{len(matches)} 条"]
    for item in matches:
        lines.extend(
            [
                "",
                f"- [{item['type']}] {item['id']} {item['title']} ({item['status']})",
                f"  路径：{item['path']}",
                f"  摘要：{item['summary'] or '-'}",
                f"  命中：{'；'.join(item['matched_by'])}",
                f"  失效信号：{'、'.join(item['failure_signals']) or '-'}",
            ]
        )
        if full:
            lines.extend(["", item["content"].rstrip()])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="汇总生命周期状态")
    summary_parser.add_argument("--json", action="store_true")

    index_parser = subparsers.add_parser("rebuild-index", help="重建三个短索引")
    index_parser.add_argument("--apply", action="store_true")

    load_parser = subparsers.add_parser("load", help="按研究场景选择性加载知识")
    load_parser.add_argument("--context", default="")
    load_parser.add_argument("--types", nargs="+", choices=sorted(TYPE_PATHS), default=sorted(TYPE_PATHS))
    load_parser.add_argument("--domain", action="append", default=[])
    load_parser.add_argument("--ticker", action="append", default=[])
    load_parser.add_argument("--scenario", action="append", default=[])
    load_parser.add_argument("--signal", action="append", default=[])
    load_parser.add_argument("--limit", type=int, default=8)
    load_parser.add_argument("--include-review", action="store_true")
    load_parser.add_argument("--all-active", action="store_true")
    load_parser.add_argument("--full", action="store_true")
    load_parser.add_argument("--json", action="store_true")
    load_parser.add_argument("--record", action="store_true")
    load_parser.add_argument("--research-id", default="")

    transition_parser = subparsers.add_parser("transition", help="预览或执行合法状态迁移")
    transition_parser.add_argument("path", type=Path)
    transition_parser.add_argument("--to", required=True)
    transition_parser.add_argument("--reason", required=True)
    transition_parser.add_argument("--evidence", action="append", default=[])
    transition_parser.add_argument("--queue", action="store_true", help="追加到待确认队列，不改变知识状态")
    transition_parser.add_argument("--apply", action="store_true")
    transition_parser.add_argument("--confirmed", action="store_true")

    args = parser.parse_args()
    root = find_workspace_root(args.root)
    if args.command == "summary":
        result = summarize(root)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("知识生命周期摘要")
            for knowledge_type in TYPE_PATHS:
                values = result["counts"].get(knowledge_type, {})
                print(f"- {knowledge_type}: " + (", ".join(f"{key}={value}" for key, value in sorted(values.items())) or "0"))
            print(f"- 到期复审：{len(result['overdue'])}")
            print(f"- 晋级候选：{len(result['promotion_candidates'])}")
        return 0
    if args.command == "rebuild-index":
        result = rebuild_indexes(root, args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "load":
        if not args.context and not args.all_active and not any((args.domain, args.ticker, args.scenario, args.signal)):
            print("ERROR: 请提供 --context、结构化筛选，或显式使用 --all-active", file=sys.stderr)
            return 2
        matches = load_knowledge(
            root,
            context=args.context,
            selected_types=set(args.types),
            limit=max(1, args.limit),
            include_review=args.include_review,
            all_active=args.all_active,
            filters={
                "domain": args.domain,
                "ticker": args.ticker,
                "decision_scenarios": args.scenario,
                "recall_signals": args.signal,
            },
        )
        invocation_id = record_load(root, args.context, matches, args.research_id) if args.record else None
        if args.json:
            payload = {"invocation_id": invocation_id, "matches": matches}
            if not args.full:
                for item in payload["matches"]:
                    item.pop("content", None)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(render_load(matches, args.full))
            if invocation_id:
                print(f"\n调用记录：{invocation_id}")
        return 0

    page = find_page(root, args.path)
    if page is None:
        print(f"ERROR: 不是受支持的知识卡：{args.path}", file=sys.stderr)
        return 2
    if args.to not in STATUSES[page["type"]]:
        print(f"ERROR: `{args.to}` 不是 {page['type']} 的合法状态", file=sys.stderr)
        return 2
    errors = transition_errors(page, args.to)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    preview = {
        "path": page["relative_path"],
        "id": page["meta"].get("id"),
        "from": page["meta"].get("status"),
        "to": args.to,
        "reason": args.reason,
        "evidence": args.evidence,
        "applied": False,
    }
    if args.queue:
        item, created = queue_transition(root, page, args.to, args.reason, args.evidence)
        preview["queued"] = {"created": created, "item": item}
    if args.apply:
        if not args.confirmed:
            print("ERROR: 状态变更必须同时提供 --confirmed，表示用户已确认", file=sys.stderr)
            return 2
        apply_transition(page["path"], args.to, args.reason, args.evidence)
        rebuild_indexes(root, True)
        preview["applied"] = True
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
