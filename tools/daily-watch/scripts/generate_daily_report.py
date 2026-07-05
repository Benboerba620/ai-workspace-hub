from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values

from workspace_paths import (
    find_workspace_root,
    resolve_config_dir,
    resolve_config_path,
    resolve_env_path,
    resolve_hypothesis_dir,
    resolve_template_path,
)

# Windows 控制台可能默认 cp1252/GBK，统一 UTF-8 输出避免中文触发 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.is_file():
        log(f"Warning: {env_path} not found; continuing without API keys")
        return {}
    raw_text = env_path.read_text(encoding="utf-8-sig")
    parsed = dotenv_values(stream=StringIO(raw_text))
    values: dict[str, str] = {}
    for key, value in parsed.items():
        if value is None:
            continue
        values[key] = value
        if key not in os.environ:
            os.environ[key] = value
    return values


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8-sig") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"配置文件 {config_path} 必须是映射结构")
    return payload


def run_json_script(workspace_root: Path, script_name: str) -> dict[str, Any]:
    local_scripts = Path(__file__).resolve().parent
    script_path = local_scripts / script_name
    if not script_path.exists():
        script_path = workspace_root / "scripts" / script_name
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.stderr.strip():
        log(completed.stderr.strip())
    if completed.returncode != 0:
        raise RuntimeError(
            f"{script_name} exited with code {completed.returncode}; "
            "see the log output above for the underlying error"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{script_name} did not produce valid JSON: {exc}") from exc


def format_pct(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):+.2f}%"


def format_num(value: Any, digits: int = 2, prefix: str = "") -> str:
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return f"{prefix}{value}"
    if isinstance(value, float):
        return f"{prefix}{value:.{digits}f}"
    return f"{prefix}{value}"


def status_from_change(value: Any) -> str:
    if value is None:
        return "N/A"
    numeric = float(value)
    if numeric > 1:
        return "强势"
    if numeric > 0:
        return "上涨"
    if numeric < -1:
        return "偏弱"
    if numeric < 0:
        return "下跌"
    return "持平"


def translate_sentiment(value: Any) -> str:
    if value is None:
        return "N/A"

    mapping = {
        "Optimistic": "乐观",
        "Normal": "中性",
        "Cautious": "谨慎",
        "Panic": "恐慌",
        "Unknown": "未知",
        "risk-on": "风险偏好回升",
        "risk-off": "风险偏好下降",
    }
    text = str(value).strip()
    if not text:
        return "N/A"
    parts = [part.strip() for part in text.split(",") if part.strip()]
    translated = [mapping.get(part, part) for part in parts]
    return "，".join(translated) if translated else "N/A"


class SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def normalize_modules(config: dict[str, Any]) -> dict[str, bool]:
    modules = config.get("modules") or {}
    if not isinstance(modules, dict):
        modules = {}
    return {
        "macro": bool(modules.get("macro", True)),
        "earnings": bool(modules.get("earnings", True)),
        "focus_areas": bool(modules.get("focus_areas", True)),
    }


def build_macro_defaults() -> dict[str, dict[str, Any]]:
    return {
        "VIX": {"price": None, "change_pct": None, "status": "N/A"},
        "SPY": {"price": None, "change_pct": None},
        "QQQ": {"price": None, "change_pct": None},
        "GLD": {"price": None, "change_pct": None},
        "CLUSD": {"price": None, "change_pct": None},
        "BTC": {"price": None, "change_pct": None},
    }


def render_market_overview(
    macro_data: dict[str, Any], enabled: bool
) -> tuple[str, str]:
    macro = build_macro_defaults()
    if enabled:
        macro.update(macro_data.get("macro") or {})
        summary = translate_sentiment(macro_data.get("sentiment") or "N/A")
    else:
        summary = "宏观模块已关闭"

    rows = [
        "| 指标 | 数值 | 涨跌幅 | 状态 |",
        "|------|------|--------|------|",
        (
            f"| VIX | {format_num(macro['VIX'].get('price'))} | "
            f"{format_pct(macro['VIX'].get('change_pct'))} | "
            f"{translate_sentiment(macro['VIX'].get('status', 'N/A'))} |"
        ),
        (
            f"| SPY | {format_num(macro['SPY'].get('price'))} | "
            f"{format_pct(macro['SPY'].get('change_pct'))} | "
            f"{status_from_change(macro['SPY'].get('change_pct'))} |"
        ),
        (
            f"| QQQ | {format_num(macro['QQQ'].get('price'))} | "
            f"{format_pct(macro['QQQ'].get('change_pct'))} | "
            f"{status_from_change(macro['QQQ'].get('change_pct'))} |"
        ),
        (
            f"| GLD | {format_num(macro['GLD'].get('price'))} | "
            f"{format_pct(macro['GLD'].get('change_pct'))} | "
            f"{status_from_change(macro['GLD'].get('change_pct'))} |"
        ),
        (
            f"| WTI | {format_num(macro['CLUSD'].get('price'))} | "
            f"{format_pct(macro['CLUSD'].get('change_pct'))} | "
            f"{status_from_change(macro['CLUSD'].get('change_pct'))} |"
        ),
        (
            f"| BTC | {format_num(macro['BTC'].get('price'), prefix='$')} | "
            f"{format_pct(macro['BTC'].get('change_pct'))} | "
            f"{status_from_change(macro['BTC'].get('change_pct'))} |"
        ),
    ]
    return "\n".join(rows), summary


def render_key_movers(movers: list[dict[str, Any]]) -> str:
    rows = [
        "| 代码 | 名称 | 涨跌幅 | 分类 | 摘要 |",
        "|------|------|--------|------|------|",
    ]
    if movers:
        for mover in movers[:10]:
            change = format_pct(mover["changesPercentage"])
            rows.append(
                f"| {mover['ticker']} | {mover['name']} | {change} | "
                f"{mover['category']} | 用 WebSearch 补充新闻与原因分析 |"
            )
    else:
        rows.append("| 暂无 | 当前没有股票超过异动阈值 | N/A | N/A | 无需补充 |")
    return "\n".join(rows)


def render_other_movers(
    quotes: list[dict[str, Any]], movers: list[dict[str, Any]] | None = None
) -> str:
    rows = [
        "| 代码 | 名称 | 涨跌幅 |",
        "|------|------|--------|",
    ]
    mover_tickers = {item["ticker"] for item in (movers or []) if "ticker" in item}
    other_movers = sorted(
        [
            item
            for item in quotes
            if item.get("changesPercentage") is not None
            and item.get("ticker") not in mover_tickers
        ],
        key=lambda item: abs(float(item["changesPercentage"])),
        reverse=True,
    )[:5]
    if other_movers:
        for mover in other_movers:
            change = format_pct(mover["changesPercentage"])
            rows.append(
                f"| {mover['ticker']} | {mover['name']} | {change} |"
            )
    else:
        rows.append("| 暂无 | 当前没有可展示的其他异动 | N/A |")
    return "\n".join(rows)


def render_earnings_sections(
    earnings: list[dict[str, Any]], enabled: bool
) -> tuple[str, str]:
    reported_rows = [
        "| 代码 | 日期 | 预期 EPS | 实际 EPS | Surprise | 市场反应 |",
        "|------|------|----------|----------|----------|----------|",
    ]
    upcoming_rows = [
        "| 代码 | 日期 | 预期 EPS |",
        "|------|------|----------|",
    ]
    if not enabled:
        reported_rows.append("| 模块关闭 | N/A | N/A | N/A | N/A | 财报模块已关闭 |")
        upcoming_rows.append("| 模块关闭 | N/A | N/A |")
        return "\n".join(reported_rows), "\n".join(upcoming_rows)

    if earnings:
        for item in earnings[:10]:
            actual_eps = item.get("eps")
            estimated_eps = item.get("epsEstimated")
            surprise = (
                format_num(actual_eps - estimated_eps, digits=2)
                if isinstance(actual_eps, (int, float))
                and isinstance(estimated_eps, (int, float))
                else "N/A"
            )
            if actual_eps is not None:
                estimated = estimated_eps if estimated_eps is not None else "N/A"
                reported_rows.append(
                    f"| {item['ticker']} | {item.get('date') or 'N/A'} | {estimated} | "
                    f"{actual_eps} | {surprise} | 用 WebSearch 补充市场反应 |"
                )
            else:
                estimated = estimated_eps if estimated_eps is not None else "N/A"
                upcoming_rows.append(
                    f"| {item['ticker']} | {item.get('date') or 'N/A'} | {estimated} |"
                )

    if len(reported_rows) == 2:
        reported_rows.append(
            "| 暂无 | N/A | N/A | N/A | N/A | 当前没有已披露财报条目 |"
        )
    if len(upcoming_rows) == 2:
        upcoming_rows.append("| 暂无 | N/A | N/A |")
    return "\n".join(reported_rows), "\n".join(upcoming_rows)


def render_themes(config: dict[str, Any], enabled: bool) -> str:
    if not enabled:
        return "### 模块关闭\n\n- `focus_areas` 模块已关闭。"

    focus_areas = config.get("focus_areas") or []
    if not focus_areas:
        return "### 暂无\n\n- 当前配置未设置 focus areas。"

    blocks: list[str] = []
    for area in focus_areas[:3]:
        name = str(area.get("name") or "未命名主题")
        keywords = "、".join(str(item) for item in area.get("keywords") or [])
        blocks.append(f"### {name}")
        blocks.append("")
        blocks.append(f"- 关键词：{keywords or '未配置'}")
        blocks.append("- 用 Claude Code WebSearch 进行主题新闻检索并在核实来源后写入。")
        blocks.append("")
    return "\n".join(blocks).rstrip()


def render_sources(modules: dict[str, bool]) -> str:
    lines = ["- `fetch_market_data.py`：拉取监控池当前或最近可用行情、异动和财报数据"]
    if modules["macro"]:
        lines.append("- `fetch_macro_data.py`：配置 FMP 后拉取 VIX、指数、商品和 BTC 数据")
    else:
        lines.append("- `fetch_macro_data.py`：当前配置已关闭宏观模块，本次未调用")
    lines.append(
        "- 新闻部分：由 Claude Code 通过 WebSearch 补充，不能用本地行情接口替代"
    )
    lines.append("- 假设联动部分：由本地 hypothesis 文件扫描生成，结论需要人工确认")
    return "\n".join(lines)


def load_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8-sig")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-") or "hypothesis"


def extract_frontmatter(content: str) -> dict[str, Any]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not match:
        return {}
    try:
        payload = yaml.safe_load(match.group(1)) or {}
        return payload if isinstance(payload, dict) else {}
    except yaml.YAMLError:
        return {}


def extract_title(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(H\d+)\s*[:：]\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(2).strip()
    return fallback


# Ticker shapes accepted in the 关联标的 table (first column):
# - US style, optional share class: F, NVDA, BRK.B, BF-B
# - Numeric codes with a market suffix: 601857.SH, 0700.HK, 005930.KS
# The cell must already be written in uppercase; mixed-case words such as
# company names ("Apple") are intentionally rejected to avoid false positives.
RELATED_TICKER_PATTERN = re.compile(
    r"[A-Z][A-Z0-9]{0,4}(?:[.-][A-Z0-9]{1,2})?"
    r"|\d{4,6}\.[A-Z]{1,2}"
)


def extract_related_tickers(content: str) -> set[str]:
    tickers: set[str] = set()
    section_match = re.search(
        r"##\s*关联标的(.*?)(?:\n##\s|\Z)", content, re.DOTALL
    )
    if section_match:
        section = section_match.group(1)
        for line in section.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and cells[0] and cells[0] != "公司" and set(cells[0]) != {"-"}:
                candidate = cells[0]
                if candidate != candidate.upper():
                    continue
                if RELATED_TICKER_PATTERN.fullmatch(candidate):
                    tickers.add(candidate)
    return tickers


def keyword_matches_text(keyword: str, haystack: str) -> bool:
    normalized = keyword.strip().lower()
    if not normalized:
        return False
    if re.fullmatch(r"[a-z0-9][a-z0-9\s-]*", normalized):
        pattern = rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])"
        return re.search(pattern, haystack) is not None
    return normalized in haystack


def read_hypotheses(workspace_root: Path) -> list[dict[str, Any]]:
    hypothesis_dir = resolve_hypothesis_dir(workspace_root)
    if not hypothesis_dir.exists():
        return []

    items: list[dict[str, Any]] = []
    for file_path in sorted(hypothesis_dir.glob("H*.md")):
        content = file_path.read_text(encoding="utf-8-sig")
        frontmatter = extract_frontmatter(content)
        fallback_title = file_path.stem
        items.append(
            {
                "id": re.match(r"(H\d+)", file_path.stem).group(1)
                if re.match(r"(H\d+)", file_path.stem)
                else file_path.stem,
                "title": extract_title(content, fallback_title),
                "certainty": frontmatter.get("certainty"),
                "status": frontmatter.get("status"),
                "tickers": extract_related_tickers(content),
                "content": content,
                "path": file_path,
            }
        )
    return items


def collect_hypothesis_signals(
    hypotheses: list[dict[str, Any]],
    config: dict[str, Any],
    movers: list[dict[str, Any]],
    earnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    signal_keys: set[tuple[str, str, str]] = set()

    for hypothesis in hypotheses:
        for mover in movers[:10]:
            ticker = str(mover.get("ticker", "")).upper()
            if not ticker or ticker not in hypothesis["tickers"]:
                continue
            key = (hypothesis["id"], "mover", ticker)
            if key in signal_keys:
                continue
            signal_keys.add(key)
            change = format_pct(mover.get("changesPercentage"))
            signals.append(
                {
                    "hypothesis_id": hypothesis["id"],
                    "hypothesis_title": hypothesis["title"],
                    "signal_type": "mover",
                    "ref": ticker,
                    "display": (
                        f"- {hypothesis['id']} `{hypothesis['title']}` "
                        f"<- {ticker} {change}，建议补充今日异动原因和证据判断。"
                    ),
                    "summary": (
                        f"{ticker} 今日涨跌幅 {change}，"
                        f"分类 {mover.get('category', 'N/A')}"
                    ),
                    "auto_writeback": True,
                }
            )

        for earning in earnings[:10]:
            ticker = str(earning.get("ticker", "")).upper()
            if not ticker or ticker not in hypothesis["tickers"]:
                continue
            key = (hypothesis["id"], "earnings", ticker)
            if key in signal_keys:
                continue
            signal_keys.add(key)
            estimated = earning.get("epsEstimated")
            actual = earning.get("eps")
            surprise = "N/A"
            if isinstance(estimated, (int, float)) and isinstance(actual, (int, float)):
                surprise = format_num(actual - estimated, digits=2)
            signals.append(
                {
                    "hypothesis_id": hypothesis["id"],
                    "hypothesis_title": hypothesis["title"],
                    "signal_type": "earnings",
                    "ref": ticker,
                    "display": (
                        f"- {hypothesis['id']} `{hypothesis['title']}` "
                        f"<- {ticker} 财报事件，建议核对财报是否强化或削弱原假设。"
                    ),
                    "summary": (
                        f"{ticker} 财报：实际 EPS "
                        f"{actual if actual is not None else 'N/A'}，"
                        f"预期 EPS {estimated if estimated is not None else 'N/A'}，"
                        f"surprise {surprise}"
                    ),
                    "auto_writeback": True,
                }
            )

    focus_areas = config.get("focus_areas") or []
    for hypothesis in hypotheses:
        for area in focus_areas[:3]:
            if not matches_focus_area(hypothesis, area):
                continue
            name = str(area.get("name") or "未命名主题")
            key = (hypothesis["id"], "theme", name)
            if key in signal_keys:
                continue
            signal_keys.add(key)
            signals.append(
                {
                    "hypothesis_id": hypothesis["id"],
                    "hypothesis_title": hypothesis["title"],
                    "signal_type": "theme",
                    "ref": name,
                    "display": (
                        f"- {hypothesis['id']} `{hypothesis['title']}` "
                        f"命中主题 `{name}`，如果今天相关新闻密集，建议更新证据时间线。"
                    ),
                    "summary": f"主题 `{name}` 在今日 watchlist 中仍为重点跟踪方向",
                    "auto_writeback": False,
                }
            )

    return signals


def matches_focus_area(hypothesis: dict[str, Any], area: dict[str, Any]) -> bool:
    haystack = f"{hypothesis['title']}\n{hypothesis['content']}".lower()
    keywords = [str(item).lower() for item in area.get("keywords") or []]
    required_any = [str(item).lower() for item in area.get("required_any") or []]
    excluded = [str(item).lower() for item in area.get("exclude") or []]
    if any(keyword_matches_text(keyword, haystack) for keyword in excluded):
        return False
    if required_any and not any(
        keyword_matches_text(keyword, haystack) for keyword in required_any
    ):
        return False
    return (
        any(keyword_matches_text(keyword, haystack) for keyword in keywords)
        if keywords
        else False
    )


def format_certainty(certainty: Any) -> str:
    if certainty is None:
        return "N/A"
    return f"{certainty}%"


def hypothesis_settings(config: dict[str, Any]) -> tuple[bool, bool]:
    """Return (enabled, auto_writeback) from config.hypothesis_tracking.

    Both default to True to preserve backwards-compatible behavior.
    """
    hypothesis_config = config.get("hypothesis_tracking") or {}
    if not isinstance(hypothesis_config, dict):
        hypothesis_config = {}
    enabled = bool(hypothesis_config.get("enabled", True))
    auto_writeback = bool(hypothesis_config.get("auto_writeback", True))
    return enabled, auto_writeback


def build_hypothesis_section(
    hypotheses: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    config: dict[str, Any],
) -> str:
    hypothesis_config = config.get("hypothesis_tracking") or {}
    if not hypothesis_config.get("enabled", True):
        return "### 模块关闭\n\n- `hypothesis_tracking.enabled` 已关闭。"

    if not hypotheses:
        return (
            "### 当前状态\n\n"
            "- 当前还没有任何 hypothesis 文件。\n"
            "- 如果今天出现重复主题或强信号，建议运行 `/ht-new` 建立第一条投资假设。"
        )

    lines: list[str] = []
    lines.append("### 已追踪假设概览")
    lines.append("")
    lines.append("| ID | 名称 | 确定性 | 状态 | 关联标的 |")
    lines.append("|----|------|--------|------|----------|")
    for item in hypotheses:
        tickers = "、".join(sorted(item["tickers"])) if item["tickers"] else "N/A"
        lines.append(
            f"| {item['id']} | {item['title']} | "
            f"{format_certainty(item['certainty'])} | "
            f"{item.get('status') or 'N/A'} | {tickers} |"
        )

    lines.append("")
    lines.append("### 今日触发信号")
    lines.append("")
    if signals:
        max_matches = int(hypothesis_config.get("max_matches", 8))
        lines.extend(signal["display"] for signal in signals[:max_matches])
    else:
        lines.append("- 今天没有发现与现有假设明显命中的个股或主题。")

    lines.append("")
    lines.append("### 操作建议")
    lines.append("")
    if signals:
        if hypothesis_config.get("auto_writeback", True):
            lines.append("- 已将本地可确认信号自动回写到对应 `hypothesis/H*.md`。")
        else:
            lines.append(
                "- `auto_writeback` 已关闭：以上信号仅在日报中展示，未回写假设文件。"
            )
        lines.append("- 如需整体回看当前假设状态，运行 `/ht-status`。")
    else:
        lines.append(
            "- 如果今日重复出现某个主题，考虑运行 `/ht-new` 建立新的跟踪假设。"
        )
    lines.append("- 如果今天已经发生买卖动作，运行 `/ht-trade` 记录交易并回写假设。")

    return "\n".join(lines)


def build_signal_marker(date_text: str, signal: dict[str, Any]) -> str:
    signal_type = str(signal["signal_type"])
    ref = slugify(str(signal["ref"]))
    return f"DW-{date_text}-{signal_type}-{ref}"


def render_signal_evidence(
    date_text: str, signal: dict[str, Any], report_relpath: str
) -> str:
    marker = build_signal_marker(date_text, signal)
    return "\n".join(
        [
            f"- 🟡 **[{marker}] Daily Watchlist** - {signal['summary']}",
            f"  - 来源：{report_relpath}",
            "  - 影响：日报自动回写，待结合新闻后再决定是否调整确定性。",
        ]
    )


def append_to_date_block(section_body: str, date_text: str, entry_text: str) -> str:
    date_pattern = re.compile(
        rf"(?ms)^###\s*{re.escape(date_text)}\s*\n(.*?)(?=^###\s|^##\s|^---\s*$|\Z)"
    )
    match = date_pattern.search(section_body)
    if match:
        block = match.group(0).rstrip()
        updated = block + "\n" + entry_text + "\n"
        return section_body[: match.start()] + updated + section_body[match.end() :]

    addition = f"\n\n### {date_text}\n\n{entry_text}\n"
    # If the section ends with a horizontal rule ("---"), insert the new date
    # block before it so entries stay inside the section instead of drifting
    # past the visual separator.
    trailing_rule = re.search(r"(?ms)\n-{3,}[ \t]*\n?\s*\Z", section_body)
    if trailing_rule:
        head = section_body[: trailing_rule.start()].rstrip()
        tail = section_body[trailing_rule.start() :]
        return head + addition + tail
    suffix = "\n" if not section_body.endswith("\n") else ""
    return section_body.rstrip() + addition + suffix


def append_signal_to_hypothesis(
    content: str, date_text: str, signal: dict[str, Any], report_relpath: str
) -> tuple[str, bool]:
    marker = build_signal_marker(date_text, signal)
    if marker in content:
        return content, False

    entry_text = render_signal_evidence(date_text, signal, report_relpath)
    section_pattern = re.compile(r"(?ms)^##\s*证据时间线\s*\n(.*?)(?=^##\s|\Z)")
    match = section_pattern.search(content)
    if not match:
        appended = (
            content.rstrip()
            + "\n\n## 证据时间线\n\n"
            + f"### {date_text}\n\n{entry_text}\n"
        )
        return appended, True

    updated_body = append_to_date_block(match.group(1), date_text, entry_text)
    updated_content = content[: match.start(1)] + updated_body + content[match.end(1) :]
    return updated_content, True


def apply_hypothesis_updates(
    workspace_root: Path,
    hypotheses: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    report_path: Path,
    date_text: str,
) -> int:
    report_relpath = str(report_path.relative_to(workspace_root)).replace("\\", "/")
    hypothesis_map = {item["id"]: item for item in hypotheses}
    writeback_count = 0

    for signal in signals:
        if not signal.get("auto_writeback"):
            continue
        hypothesis = hypothesis_map.get(str(signal["hypothesis_id"]))
        if not hypothesis:
            continue
        path = Path(hypothesis["path"])
        original = path.read_text(encoding="utf-8")
        updated, changed = append_signal_to_hypothesis(
            original, date_text, signal, report_relpath
        )
        if changed and updated != original:
            path.write_text(updated, encoding="utf-8")
            writeback_count += 1

    return writeback_count


def build_report(
    workspace_root: Path,
    config: dict[str, Any],
    template_text: str,
    market_data: dict[str, Any],
    macro_data: dict[str, Any],
    hypotheses: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> Path:
    today = date.today()
    weekday_map = {
        "Monday": "星期一",
        "Tuesday": "星期二",
        "Wednesday": "星期三",
        "Thursday": "星期四",
        "Friday": "星期五",
        "Saturday": "星期六",
        "Sunday": "星期日",
    }
    weekday = weekday_map[today.strftime("%A")]
    report_dir = workspace_root / "daily-watchlist-reports" / today.strftime("%Y-%m")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{today.isoformat()}.md"

    modules = normalize_modules(config)
    quotes = market_data.get("quotes") or []
    movers = market_data.get("movers") or []
    earnings = market_data.get("earnings") or []
    market_table, market_summary = render_market_overview(macro_data, modules["macro"])
    earnings_reported, earnings_upcoming = render_earnings_sections(
        earnings, modules["earnings"]
    )
    context = SafeFormatDict(
        DATE=today.isoformat(),
        WEEKDAY=weekday,
        REPORT_NOTE=(
            "> 说明：本文件由本地脚本先生成数据骨架。新闻检索、原因分析与主题研究应由 "
            "Claude Code 在运行 `/dw-today` 时通过 WebSearch 补充。"
        ),
        MARKET_OVERVIEW_TABLE=market_table,
        MARKET_SUMMARY=market_summary,
        KEY_MOVERS_TABLE=render_key_movers(movers),
        OTHER_MOVERS_TABLE=render_other_movers(quotes, movers),
        EARNINGS_REPORTED_TABLE=earnings_reported,
        EARNINGS_UPCOMING_TABLE=earnings_upcoming,
        THEMES_SECTION=render_themes(config, modules["focus_areas"]),
        HYPOTHESIS_SECTION=build_hypothesis_section(hypotheses, signals, config),
        SOURCES_SECTION=render_sources(modules),
    )
    rendered = template_text.format_map(context).rstrip() + "\n"
    report_path.write_text(rendered, encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the daily watchlist report (market data, macro, hypothesis signals)."
    )
    parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    workspace_root = find_workspace_root(script_dir)
    config_dir = resolve_config_dir(workspace_root)
    load_env_file(resolve_env_path(config_dir))
    config = load_config(resolve_config_path(config_dir))
    modules = normalize_modules(config)
    template_text = load_template(resolve_template_path(workspace_root))

    market_data = run_json_script(workspace_root, "fetch_market_data.py")
    macro_data = (
        run_json_script(workspace_root, "fetch_macro_data.py")
        if modules["macro"]
        else {}
    )
    movers = market_data.get("movers") or []
    earnings = market_data.get("earnings") or []
    hypothesis_enabled, auto_writeback = hypothesis_settings(config)
    hypotheses = read_hypotheses(workspace_root) if hypothesis_enabled else []
    signals = (
        collect_hypothesis_signals(hypotheses, config, movers, earnings)
        if hypothesis_enabled
        else []
    )
    report_path = build_report(
        workspace_root,
        config,
        template_text,
        market_data,
        macro_data,
        hypotheses,
        signals,
    )
    if hypothesis_enabled and auto_writeback:
        apply_hypothesis_updates(
            workspace_root, hypotheses, signals, report_path, date.today().isoformat()
        )
    print(json.dumps({"report_path": str(report_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
