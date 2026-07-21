#!/usr/bin/env python3
"""Build a compact, verifiable local-knowledge package before research."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import knowledge_lifecycle as lifecycle  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

WIKI_SECTIONS = ("entities", "concepts", "sources")
SECTION_TYPES = {"entities": "entity", "concepts": "concept", "sources": "source", "raw": "raw"}
KNOWLEDGE_SECTIONS = {
    "exploration": "explorations",
    "pattern": "patterns",
    "rule": "rules",
}
REVIEW_STATUSES = {
    "weakened",
    "invalidated",
    "retired",
    "deprecated",
    "archived",
    "stale",
    "superseded",
}
STOP_TERMS = {
    "研究",
    "分析",
    "公司",
    "行业",
    "相关",
    "问题",
    "判断",
    "research",
    "analysis",
    "company",
}


def find_workspace_root(start: Path) -> Path:
    return lifecycle.find_workspace_root(start)


def resolve_wiki_root(root: Path, requested: Path | None = None) -> Path:
    if requested is not None:
        candidate = requested.expanduser()
    else:
        candidate = Path("wiki")
        config = root / "workspace" / "workspace-config.md"
        if config.is_file():
            content = config.read_text(encoding="utf-8-sig")
            match = re.search(
                r"(?m)^\s*-\s*wiki_root:\s*`?([^`\r\n]+?)`?\s*$", content
            )
            if match:
                candidate = Path(match.group(1).strip().strip('"\''))
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def display_path(path: Path, root: Path) -> str:
    try:
        return lifecycle.relative(path, root)
    except ValueError:
        return str(path)


def as_list(value: Any) -> list[str]:
    return lifecycle.as_list(value)


def normalize(value: str) -> str:
    return lifecycle.normalized(value)


def query_terms(context: str, explicit: list[str]) -> list[str]:
    terms = [item.strip() for item in explicit if item.strip()]
    terms.extend(
        item.strip()
        for item in re.split(r"[\s,，。；;:：/|、()（）]+", context)
        if item.strip()
    )
    terms.extend(re.findall(r"\b[A-Za-z]{1,8}(?:\.[A-Za-z]{1,4})?\b", context))
    result: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = normalize(term)
        if len(key) < 2 or key in STOP_TERMS or key in seen:
            continue
        seen.add(key)
        result.append(term)
    return result


def extract_title(meta: dict[str, Any], content: str, path: Path) -> str:
    if meta.get("title"):
        return str(meta["title"])
    match = re.search(r"(?m)^#\s+(.+?)\s*$", content)
    return match.group(1).strip() if match else path.stem


def strip_frontmatter(content: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*(?:\n|$)", "", content, count=1, flags=re.DOTALL)


def make_snippet(content: str, terms: list[str], limit: int = 260) -> str:
    body = strip_frontmatter(content)
    lines = [line.strip(" #>-\t") for line in body.splitlines() if line.strip()]
    normalized_terms = [normalize(term) for term in terms]
    for line in lines:
        normalized_line = normalize(line)
        if any(term in normalized_line for term in normalized_terms if term):
            return line[:limit] + ("…" if len(line) > limit else "")
    if not lines:
        return ""
    text = " ".join(lines[:3])
    return text[:limit] + ("…" if len(text) > limit else "")


def substantive_counter_section(content: str) -> bool:
    pattern = re.compile(
        r"(?ims)^##\s*(?:反方证据|反例|矛盾|争议|counter[- ]?evidence|counterexamples?)\s*$"
        r"(.*?)(?=^##\s|\Z)"
    )
    for match in pattern.finditer(content):
        body = re.sub(r"<!--[\s\S]*?-->", "", match.group(1))
        body = re.sub(r"[\s#>*_`-]", "", body)
        if body:
            return True
    return False


def page_flags(section: str, meta: dict[str, Any], content: str) -> list[str]:
    flags: list[str] = []
    status = str(meta.get("status") or "").lower()
    if status in REVIEW_STATUSES:
        flags.append(f"状态需复审: {status}")
    if lifecycle.is_overdue(meta.get("review_due")):
        flags.append(f"复审已到期: {meta.get('review_due')}")
    if substantive_counter_section(content):
        flags.append("存在已填写的反方/冲突章节")
    if section == "sources" and not (meta.get("source_url") or meta.get("source_path")):
        flags.append("来源字段不完整")
    if section in KNOWLEDGE_SECTIONS:
        if not meta.get("id"):
            flags.append("缺少稳定知识 ID")
        if not meta.get("review_due"):
            flags.append("缺少复审日期")
        if not as_list(meta.get("recall_signals")):
            flags.append("缺少召回信号")
    return flags


def score_wiki_page(
    *,
    meta: dict[str, Any],
    title: str,
    path: Path,
    content: str,
    context: str,
    terms: list[str],
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    context_norm = normalize(context)
    title_norm = normalize(title)
    filename_norm = normalize(path.stem)
    body_norm = normalize(strip_frontmatter(content))

    weighted_fields = (
        ("ticker", 14, "标的"),
        ("concepts", 9, "概念"),
        ("tags", 7, "标签"),
        ("related", 6, "关联页"),
        ("domain", 3, "领域"),
    )
    for field, weight, label in weighted_fields:
        hits = []
        for value in as_list(meta.get(field)):
            value_norm = normalize(value)
            if value_norm and value_norm in context_norm:
                hits.append(value)
        if hits:
            score += weight * len(hits)
            reasons.append(f"{label}: {'、'.join(hits[:2])}")

    title_hits = [term for term in terms if normalize(term) in title_norm or normalize(term) in filename_norm]
    if title_hits:
        score += 10 * len(title_hits)
        reasons.append("标题: " + "、".join(title_hits[:3]))
    elif len(title_norm) >= 3 and title_norm in context_norm:
        score += 12
        reasons.append(f"标题直接命中: {title}")

    body_hits = [term for term in terms if normalize(term) in body_norm]
    if body_hits:
        score += 2 * min(len(body_hits), 5)
        reasons.append("正文: " + "、".join(body_hits[:3]))

    summary_norm = normalize(str(meta.get("summary") or meta.get("description") or ""))
    summary_hits = [term for term in terms if normalize(term) in summary_norm]
    if summary_hits:
        score += 5 * len(summary_hits)
        reasons.append("摘要: " + "、".join(summary_hits[:3]))
    return score, reasons


def iter_knowledge_pages(root: Path, wiki_root: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    locations: list[tuple[str, Path]] = [
        (kind, wiki_root / section) for kind, section in KNOWLEDGE_SECTIONS.items()
    ]
    locations.append(("pattern", root / "workspace/patterns"))
    for knowledge_type, folder in locations:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name.startswith("_") or path.name.lower() == "readme.md":
                continue
            meta, content, error = lifecycle.read_page(path)
            pages.append(
                {
                    "type": knowledge_type,
                    "path": path,
                    "relative_path": display_path(path, root),
                    "meta": meta,
                    "content": content,
                    "error": error,
                }
            )
    return pages


def load_reusable_knowledge(
    root: Path,
    wiki_root: Path,
    context: str,
    *,
    limit: int,
    include_review: bool,
    pages: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for page in pages if pages is not None else iter_knowledge_pages(root, wiki_root):
        meta = page["meta"]
        status = str(meta.get("status") or "")
        if not include_review and status not in lifecycle.DEFAULT_LOAD_STATUSES[page["type"]]:
            continue
        score, reasons = lifecycle.score_page(page, context)
        if score <= 0:
            continue
        matches.append(
            {
                "id": str(meta.get("id") or page["path"].stem),
                "type": page["type"],
                "title": extract_title(meta, page["content"], page["path"]),
                "status": status,
                "summary": str(meta.get("summary") or ""),
                "scope": str(meta.get("scope") or ""),
                "review_due": str(meta.get("review_due") or ""),
                "failure_signals": as_list(
                    meta.get("failure_signals") or meta.get("invalidation_signals")
                ),
                "path": page["relative_path"],
                "score": score,
                "matched_by": reasons,
                "flags": page_flags(page["type"], meta, page["content"]),
                "content": page["content"],
            }
        )
    type_order = {"rule": 0, "pattern": 1, "exploration": 2}
    matches.sort(key=lambda item: (type_order[item["type"]], -item["score"], item["id"]))
    return matches[:limit]


def scan_wiki(
    root: Path,
    wiki_root: Path,
    context: str,
    terms: list[str],
    *,
    sections: tuple[str, ...],
    limit: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    matches: list[dict[str, Any]] = []
    counts = {section: 0 for section in sections}
    for section in sections:
        folder = wiki_root / section
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*.md")):
            if path.name.startswith("_") or path.name.lower() == "readme.md":
                continue
            counts[section] += 1
            meta, content, error = lifecycle.read_page(path)
            if error and not content:
                continue
            title = extract_title(meta, content, path)
            score, reasons = score_wiki_page(
                meta=meta,
                title=title,
                path=path,
                content=content,
                context=context,
                terms=terms,
            )
            if score <= 0:
                continue
            matches.append(
                {
                    "type": SECTION_TYPES[section],
                    "title": title,
                    "status": str(meta.get("status") or ""),
                    "summary": str(meta.get("summary") or meta.get("description") or ""),
                    "path": display_path(path, root),
                    "score": score,
                    "matched_by": reasons,
                    "snippet": make_snippet(content, terms),
                    "flags": page_flags(section, meta, content),
                    "content": content,
                }
            )
    section_order = {"entity": 0, "concept": 1, "source": 2, "raw": 3}
    matches.sort(key=lambda item: (-item["score"], section_order.get(item["type"], 9), item["path"]))
    return matches[:limit], counts


def build_preflight(
    root: Path,
    *,
    context: str,
    research_id: str = "",
    wiki_root: Path | None = None,
    explicit_terms: list[str] | None = None,
    tickers: list[str] | None = None,
    domains: list[str] | None = None,
    knowledge_limit: int = 8,
    wiki_limit: int = 12,
    include_review: bool = False,
    include_raw: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    root = find_workspace_root(root)
    resolved_wiki = resolve_wiki_root(root, wiki_root)
    additions = [*(explicit_terms or []), *(tickers or []), *(domains or [])]
    enriched_context = " ".join([context, *additions]).strip()
    terms = query_terms(enriched_context, additions)
    knowledge_pages = iter_knowledge_pages(root, resolved_wiki)
    knowledge = load_reusable_knowledge(
        root,
        resolved_wiki,
        enriched_context,
        limit=max(1, knowledge_limit),
        include_review=include_review,
        pages=knowledge_pages,
    )
    sections = WIKI_SECTIONS + (("raw",) if include_raw else ())
    wiki_matches, scanned = scan_wiki(
        root,
        resolved_wiki,
        enriched_context,
        terms,
        sections=sections,
        limit=max(1, wiki_limit),
    )
    digest = hashlib.sha256(
        (research_id + enriched_context + str(resolved_wiki)).encode("utf-8")
    ).hexdigest()[:8]
    prefix = re.sub(r"[^A-Za-z0-9-]+", "-", research_id).strip("-") or date.today().strftime("%Y%m%d")
    flags = [
        {"path": item["path"], "flags": item["flags"]}
        for item in [*knowledge, *wiki_matches]
        if item["flags"]
    ]
    return {
        "id": f"PF-{prefix}-{digest}",
        "research_id": research_id or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "context": enriched_context,
        "terms": terms,
        "wiki_root": str(resolved_wiki),
        "scanned": {
            "knowledge": len(knowledge_pages),
            **scanned,
        },
        "knowledge": knowledge,
        "wiki_matches": wiki_matches,
        "review_flags": flags,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in values) + "]"


def render_receipt(result: dict[str, Any]) -> str:
    knowledge_ids = [item["id"] for item in result["knowledge"]]
    wiki_paths = [item["path"] for item in result["wiki_matches"]]
    lines = [
        "---",
        f"id: {result['id']}",
        "type: research-preflight",
        f"research_id: {result['research_id'] or ''}",
        f"created_at: {result['created_at']}",
        f"context: {json.dumps(result['context'], ensure_ascii=False)}",
        f"knowledge_used: {yaml_list(knowledge_ids)}",
        f"wiki_pages_loaded: {yaml_list(wiki_paths)}",
        "---",
        "",
        f"# Research Preflight: {result['research_id'] or result['id']}",
        "",
        f"> 本地扫描耗时 {result['elapsed_ms']} ms；只记录命中和风险提示，不代表结论已验证。",
        "",
        "## 扫描范围",
        "",
        f"- Wiki：`{result['wiki_root']}`",
        "- 扫描：" + " / ".join(f"{key} {value}" for key, value in result["scanned"].items()),
        "- 检索词：" + ("、".join(result["terms"]) or "无"),
        "",
        "## 可复用知识",
        "",
    ]
    if result["knowledge"]:
        for item in result["knowledge"]:
            lines.append(
                f"- `{item['id']}` [{item['type']}] {item['title']} | {item['path']} | "
                f"命中：{'；'.join(item['matched_by'])}"
            )
    else:
        lines.append("- 未命中可复用 Rule / Pattern / Exploration。")
    lines.extend(["", "## 相关 Wiki 页面", ""])
    if result["wiki_matches"]:
        for item in result["wiki_matches"]:
            lines.append(
                f"- [{item['type']}] {item['title']} | {item['path']} | "
                f"命中：{'；'.join(item['matched_by'])} | 摘要：{item['summary'] or item['snippet'] or '-'}"
            )
    else:
        lines.append("- 未命中 Entity / Concept / Source 页面。")
    lines.extend(["", "## 复审提示", ""])
    if result["review_flags"]:
        for item in result["review_flags"]:
            lines.append(f"- {item['path']}：{'；'.join(item['flags'])}")
    else:
        lines.append("- 未发现显式过期、弱化或反方章节提示。")
    lines.extend(
        [
            "",
            "## 加载回执",
            "",
            f"Wiki check: 扫描 {sum(result['scanned'].values())} 篇，命中知识卡 "
            f"{len(result['knowledge'])} 张、普通 Wiki {len(result['wiki_matches'])} 篇；"
            f"复审提示 {len(result['review_flags'])} 条。",
            "",
        ]
    )
    return "\n".join(lines)


def save_receipt(root: Path, result: dict[str, Any], requested: Path | None = None) -> Path:
    if requested is None:
        filename = re.sub(r"[^A-Za-z0-9._-]+", "-", str(result["research_id"] or result["id"]))
        path = root / "output" / "research" / "preflight" / f"{filename}.md"
    else:
        path = requested if requested.is_absolute() else root / requested
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_receipt(result), encoding="utf-8")
    return path


def update_research_file(root: Path, requested: Path, result: dict[str, Any]) -> Path:
    path = requested if requested.is_absolute() else root / requested
    if not path.is_file():
        raise ValueError(f"research file does not exist: {display_path(path, root)}")
    meta, content, error = lifecycle.read_page(path)
    if error:
        raise ValueError(f"invalid research file: {error}")
    research_id = str(result.get("research_id") or "")
    file_id = str(meta.get("id") or "")
    if file_id and research_id and file_id != research_id:
        raise ValueError(f"research id mismatch: file={file_id}, preflight={research_id}")
    content = lifecycle.replace_frontmatter_scalar(content, "preflight_id", str(result["id"]))
    content = lifecycle.replace_frontmatter_scalar(
        content, "knowledge_used", yaml_list([item["id"] for item in result["knowledge"]])
    )
    content = lifecycle.replace_frontmatter_scalar(
        content,
        "wiki_pages_loaded",
        yaml_list([item["path"] for item in result["wiki_matches"]]),
    )
    path.write_text(content, encoding="utf-8")
    return path


def serializable_result(result: dict[str, Any], full: bool) -> dict[str, Any]:
    payload = json.loads(json.dumps(result, ensure_ascii=False))
    if not full:
        for item in [*payload["knowledge"], *payload["wiki_matches"]]:
            item.pop("content", None)
    return payload


def render_text(result: dict[str, Any], full: bool) -> str:
    lines = [render_receipt(result).rstrip()]
    if full:
        for item in [*result["knowledge"], *result["wiki_matches"]]:
            lines.extend(["", f"---\n\n## 全文：{item['title']}\n", item["content"].rstrip()])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--wiki-root", type=Path)
    parser.add_argument("--context", required=True)
    parser.add_argument("--research-id", default="")
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--ticker", action="append", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--knowledge-limit", type=int, default=8)
    parser.add_argument("--wiki-limit", type=int, default=12)
    parser.add_argument("--include-review", action="store_true")
    parser.add_argument("--include-raw", action="store_true")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--save", type=Path)
    parser.add_argument("--research-file", type=Path)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.record and (not args.research_id or not args.research_file):
        print(
            "ERROR: --record 需要同时提供 --research-id 和 --research-file，"
            "以便生成可追踪回执并更新研究报告",
            file=sys.stderr,
        )
        return 2
    root = find_workspace_root(args.root)
    result = build_preflight(
        root,
        context=args.context,
        research_id=args.research_id,
        wiki_root=args.wiki_root,
        explicit_terms=args.term,
        tickers=args.ticker,
        domains=args.domain,
        knowledge_limit=args.knowledge_limit,
        wiki_limit=args.wiki_limit,
        include_review=args.include_review,
        include_raw=args.include_raw,
    )
    if args.research_file:
        try:
            research_path = update_research_file(root, args.research_file, result)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        result["research_file"] = display_path(research_path, root)
    if args.record:
        result["knowledge_invocation_id"] = lifecycle.record_load(
            root, result["context"], result["knowledge"], args.research_id
        )
    saved = save_receipt(root, result, args.save) if args.record or args.save else None
    if saved:
        result["receipt_path"] = display_path(saved, root)
    if args.json:
        print(json.dumps(serializable_result(result, args.full), ensure_ascii=False, indent=2))
    else:
        print(render_text(result, args.full))
        if saved:
            print(f"回执：{display_path(saved, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
