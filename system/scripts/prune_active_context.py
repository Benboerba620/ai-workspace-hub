#!/usr/bin/env python3
"""Keep `workspace/meta/active-context.md` small enough to stay useful.

active-context 是工作记忆，只有「短到每次都会被读完」才有价值。手工维护做不到这点：
条目会变多、会变老、单条会越写越长，最后没人读。本脚本把上限变成可执行的闸门。

三道闸门（都只作用于 `## 最近对话延续` 段，其余段落一个字节都不动）：

1. **日期** — 超过 cutoff 天（默认 14）的条目整条剪到
   `workspace/meta/active-context-archive-YYYY-MM.md`。
2. **条数** — 剪完仍超 max_entries（默认 20）时，把最旧的几条一并归档。
3. **行长** — 单条正文超 line_cap 字节（默认 1500）时，全文进归档，
   主文件原地只留一行索引（标题 + 首个文件路径 + 存档指针）。

第 3 道是前两道够不着的地方：日期和条数都是「整条搬走」，管不住行内膨胀。
一条写成小作文的条目既不老也不多，却能单独吃掉整个文件的预算。
索引常驻 + 全文按需，是同一个文件里已经在用的办法（延续区那一行本来就是索引，
正文该写进它指向的文件）——这道闸门只是把规则变成执行。

条目的定义：顶层行 `- **YYYY-MM-DD...` 加紧随其后的所有缩进续行，
直到下一个 `- **YYYY-MM-DD`、下一个 `## ` 或文件结束。

用法：

    python3 system/scripts/prune_active_context.py              # dry-run，看看会剪什么
    python3 system/scripts/prune_active_context.py --apply      # 真正写文件
    python3 system/scripts/prune_active_context.py --cutoff 7 --apply
    python3 system/scripts/prune_active_context.py --line-cap 0 # 关掉行长闸门

幂等：归档文件只追加。整条归档按「日期 + 标题前 60 字」去重，压缩条目按内容 sha1 去重，
所以重跑不会重复追加；条目日后被改写又超长时 hash 变化会追加新版本，不会丢内容。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BYTE_CAP = 25 * 1024  # 整个文件的软上限，只警告不阻塞
LINE_CAP = 1500  # 单条目字节上限
CUTOFF_DAYS = 14
MAX_ENTRIES = 20

DATE_LINE_RE = re.compile(r"^- \*\*(\d{4})-(\d{2})-(\d{2})")
SECTION_RE = re.compile(r"^## ")
SECTION_HEADING = "## 最近对话延续"
# 条目身份（日期 + 标题前 60 字），用于整条归档时的幂等去重
ENTRY_KEY_RE = re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2}[：:][^*]{0,60})", re.M)
COMPRESSED_MARK_RE = re.compile(r"^<!-- compressed \d{4}-\d{2}-\d{2} ([0-9a-f]{8}) -->", re.M)
# 索引行里提取文件路径：优先「主产出」(.md/.html) 且非备份/临时文件，
# 取不到再退到任意后缀——否则会抓到 `_bak_xxx.csv` 这类备份名当指针，索引行就白留了。
PATH_RE = re.compile(r"`([^`\s]+\.(?:md|html|json|csv|py|xlsx))`")
PRIMARY_PATH_RE = re.compile(r"`((?:(?!_bak|_tmp|\.bak)[^`\s])+\.(?:md|html))`")

ARCHIVE_HEADER = (
    "# Active Context Archive — {month}\n\n"
    "> 从 active-context.md 「最近对话延续」滚动归档（超 {cutoff} 天 / 超条数上限 / 超行长闸门）。"
    "append-only。\n\n"
)


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    return current


def entry_hash(block_text: str) -> str:
    return hashlib.sha1(block_text.encode("utf-8")).hexdigest()[:8]


def compress_entry(block: list[str], archive_name: str, line_cap: int = LINE_CAP) -> str:
    """把一个超长条目压成单行索引：粗体标题 + 首个文件路径 + 存档指针。

    保证返回值 <= line_cap 字节（标题过长时硬截断并保持 `**` 闭合）。
    """
    text = "\n".join(block)
    match = re.match(r"^- \*\*(.+?)\*\*", block[0])
    title = match.group(1) if match else block[0].lstrip("- ").strip()[:160]
    path_match = PRIMARY_PATH_RE.search(text) or PATH_RE.search(text)
    pointer = f" → `{path_match.group(1)}`" if path_match else ""
    tail = f" …📦 全文见 `{archive_name}`"

    def build(candidate: str) -> str:
        return f"- **{candidate}**{pointer}{tail}"

    line = build(title)
    while len(line.encode("utf-8")) > line_cap and len(title) > 30:
        title = title[: max(30, len(title) - 20)].rstrip() + "…"
        line = build(title)
    return line


def find_section_bounds(lines: list[str], heading_prefix: str = SECTION_HEADING):
    """返回该段正文的 (start_inclusive, end_exclusive)，即标题行之后到下一个 `## ` 或 EOF。"""
    start = None
    for index, line in enumerate(lines):
        if line.startswith(heading_prefix):
            start = index + 1
            break
    if start is None:
        return None, None
    end = len(lines)
    for index in range(start, len(lines)):
        if SECTION_RE.match(lines[index]):
            end = index
            break
    return start, end


def parse_blocks(lines: list[str], section_start: int, section_end: int):
    """返回 [(start, end_exclusive, entry_date), ...]，只覆盖段内的顶层日期条目。"""
    blocks = []
    index = section_start
    while index < section_end:
        match = DATE_LINE_RE.match(lines[index])
        if not match:
            index += 1
            continue
        try:
            entry_date = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            index += 1
            continue
        end = index + 1
        while end < section_end:
            if DATE_LINE_RE.match(lines[end]) or SECTION_RE.match(lines[end]):
                break
            end += 1
        blocks.append((index, end, entry_date))
        index = end
    return blocks


def plan(lines: list[str], today: date, cutoff_days: int, max_entries: int, line_cap: int):
    """算出要归档 / 要压缩 / 要保留的条目，不碰文件。"""
    section_start, section_end = find_section_bounds(lines)
    if section_start is None:
        return None
    blocks = parse_blocks(lines, section_start, section_end)
    cutoff = today - timedelta(days=cutoff_days)

    to_archive = [b for b in blocks if b[2] < cutoff]
    to_keep = [b for b in blocks if b[2] >= cutoff]

    over_count = 0
    if len(to_keep) > max_entries:
        oldest_first = sorted(to_keep, key=lambda b: b[2])
        over_count = len(to_keep) - max_entries
        extras = oldest_first[:over_count]
        to_archive = to_archive + extras
        to_keep = [b for b in to_keep if b not in extras]

    to_compress = []
    if line_cap > 0:
        still_keep = []
        for block in to_keep:
            start, end, _ = block
            if len("\n".join(lines[start:end]).encode("utf-8")) > line_cap:
                to_compress.append(block)
            else:
                still_keep.append(block)
        to_keep = still_keep

    return {
        "blocks": blocks,
        "to_archive": to_archive,
        "to_compress": to_compress,
        "to_keep": to_keep,
        "over_count": over_count,
        "cutoff": cutoff,
    }


def archive_path_for(meta_dir: Path, day: date) -> Path:
    return meta_dir / f"active-context-archive-{day.strftime('%Y-%m')}.md"


def apply_plan(active: Path, meta_dir: Path, lines: list[str], result: dict,
               cutoff_days: int, line_cap: int) -> tuple[int, int]:
    """写归档文件并重写主文件，返回 (归档条数, 压缩条数)。"""
    by_archive: dict[Path, list[tuple[int, int, date, str]]] = {}
    for start, end, day in result["to_archive"]:
        by_archive.setdefault(archive_path_for(meta_dir, day), []).append((start, end, day, "archive"))
    for start, end, day in result["to_compress"]:
        by_archive.setdefault(archive_path_for(meta_dir, day), []).append((start, end, day, "compress"))

    archived = compressed = 0
    for archive_file, items in by_archive.items():
        items.sort(key=lambda item: item[2])
        existing = archive_file.read_text(encoding="utf-8") if archive_file.exists() else ""
        if not existing:
            existing = ARCHIVE_HEADER.format(
                month=items[0][2].strftime("%Y-%m"), cutoff=cutoff_days
            )
        existing_keys = {m.group(1).strip() for m in ENTRY_KEY_RE.finditer(existing)}
        existing_hashes = set(COMPRESSED_MARK_RE.findall(existing))
        appended = []
        for start, end, day, kind in items:
            body = "\n".join(lines[start:end])
            if kind == "compress":
                digest = entry_hash(body)
                if digest in existing_hashes:
                    continue
                existing_hashes.add(digest)
                appended.append(f"<!-- compressed {day.isoformat()} {digest} -->\n{body}")
                compressed += 1
                continue
            match = ENTRY_KEY_RE.match(lines[start])
            key = match.group(1).strip() if match else None
            if key and key in existing_keys:
                continue
            if key:
                existing_keys.add(key)
            appended.append(body)
            archived += 1
        if appended:
            archive_file.parent.mkdir(parents=True, exist_ok=True)
            archive_file.write_text(
                existing.rstrip() + "\n\n" + "\n\n".join(appended) + "\n", encoding="utf-8"
            )
        print(f"  ✓ wrote {archive_file.name} (+{len(appended)} 条)", file=sys.stderr)

    drop: set[int] = set()
    replace_at: dict[int, str] = {}
    for start, end, _ in result["to_archive"]:
        drop.update(range(start, end))
    for start, end, day in result["to_compress"]:
        replace_at[start] = compress_entry(
            lines[start:end], archive_path_for(meta_dir, day).name, line_cap
        )
        drop.update(range(start + 1, end))

    kept = [replace_at.get(i, line) for i, line in enumerate(lines) if i not in drop]
    folded = []
    prev_blank = False
    for line in kept:
        if line.strip() == "":
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        folded.append(line)
    active.write_text("\n".join(folded), encoding="utf-8")
    return archived, compressed


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune workspace/meta/active-context.md.")
    parser.add_argument("--root", default=None, help="工作区根目录（默认自动向上找）")
    parser.add_argument("--cutoff", type=int, default=CUTOFF_DAYS,
                        help=f"保留最近 N 天，更早的归档（默认 {CUTOFF_DAYS}）")
    parser.add_argument("--max-entries", type=int, default=MAX_ENTRIES,
                        help=f"N 天内也最多保留 M 条，超出把最旧的归档（默认 {MAX_ENTRIES}）")
    parser.add_argument("--line-cap", type=int, default=LINE_CAP,
                        help=f"单条目字节上限，超过则正文入归档、原地留索引行（默认 {LINE_CAP}；传 0 关闭）")
    parser.add_argument("--apply", action="store_true", help="实际写文件；不加则 dry-run")
    parser.add_argument("--today", default=None, help="覆盖今天日期（测试用，YYYY-MM-DD）")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else find_workspace_root(Path(__file__))
    active = root / "workspace" / "meta" / "active-context.md"
    meta_dir = active.parent
    if not active.is_file():
        print(f"ERROR: {active} not found", file=sys.stderr)
        return 1

    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    raw = active.read_text(encoding="utf-8")
    lines = raw.split("\n")

    result = plan(lines, today, args.cutoff, args.max_entries, args.line_cap)
    if result is None:
        print(f"ERROR: '{SECTION_HEADING}' section not found in {active}", file=sys.stderr)
        return 1

    print(
        f"[active-context prune] today={today} cutoff={args.cutoff}d "
        f"max_entries={args.max_entries} line_cap={args.line_cap or 'off'} "
        f"→ cutoff_date={result['cutoff']}",
        file=sys.stderr,
    )
    print(f"  条目总数: {len(result['blocks'])}", file=sys.stderr)
    print(f"  整条归档: {len(result['to_archive'])}（其中超条数上限触发 {result['over_count']}）", file=sys.stderr)
    print(f"  压成索引: {len(result['to_compress'])}（超 {args.line_cap}B 行长闸门）", file=sys.stderr)
    print(f"  原样保留: {len(result['to_keep'])}", file=sys.stderr)

    if not result["to_archive"] and not result["to_compress"]:
        size_now = active.stat().st_size
        warn = " 🔴 OVER CAP" if size_now > BYTE_CAP else ""
        print(f"  nothing to do. size={size_now}B (cap={BYTE_CAP}B){warn}", file=sys.stderr)
        if size_now > BYTE_CAP:
            print(f"  → 三道闸门已跑完仍超 {BYTE_CAP // 1024}KB，"
                  f"超标来自「最近对话延续」以外的段落，需要人工精简。", file=sys.stderr)
        return 0

    for start, _, day in result["to_archive"]:
        print(f"    归档 {day}: {lines[start][:100].rstrip()}", file=sys.stderr)
    for start, end, day in result["to_compress"]:
        original = len("\n".join(lines[start:end]).encode("utf-8"))
        index_line = compress_entry(lines[start:end], archive_path_for(meta_dir, day).name, args.line_cap)
        print(f"    压缩 {day}: {original}B → {len(index_line.encode('utf-8'))}B", file=sys.stderr)
        print(f"           {index_line[:120]}", file=sys.stderr)

    if not args.apply:
        print("\n  [dry-run] 加 --apply 实际执行", file=sys.stderr)
        return 0

    archived, compressed = apply_plan(active, meta_dir, lines, result, args.cutoff, args.line_cap)
    new_size = active.stat().st_size
    saved = len(raw.encode("utf-8")) - new_size
    warn = " 🔴 OVER CAP" if new_size > BYTE_CAP else ""
    print(f"\n  ✓ active-context.md: 归档 {archived} 条 / 压缩 {compressed} 条 / "
          f"{new_size}B（省 {saved}B，cap={BYTE_CAP}B）{warn}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
