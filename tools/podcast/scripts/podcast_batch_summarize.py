#!/usr/bin/env python3
"""Batch summarize transcript files and detect reversal-narrative red flags."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from llm_client import chat, extract_json


MAX_INPUT_CHARS = 28000
DEFAULT_REVERSAL_TRIGGERS = [
    "而非",
    "而不是",
    "颠覆",
    "反转",
    "实际上",
    "表面上",
    "打破共识",
    "并非",
    "rather than",
    "instead of",
    "actually",
]
NUMBER_RE = re.compile(r"\d[\d.,]*\s*(?:GW|MW|TW|B|M|K|%|亿|万|千|美元|元)?", re.IGNORECASE)
PROPER_RE = re.compile(r"\b[A-Z][A-Za-z0-9]{2,}\b")


def read_transcript(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= MAX_INPUT_CHARS:
        return text
    return text[: int(MAX_INPUT_CHARS * 0.75)] + "\n\n[... omitted ...]\n\n" + text[-int(MAX_INPUT_CHARS * 0.2) :]


def extract_anchors(text: str) -> tuple[list[str], list[str]]:
    numbers = [item.strip() for item in NUMBER_RE.findall(text) if any(ch.isdigit() for ch in item)]
    proper = []
    for item in PROPER_RE.findall(text):
        if item not in proper:
            proper.append(item)
    return numbers[:5], proper[:5]


def find_in_original(anchor: str, original: str, ctx: int = 150) -> str | None:
    lower = original.lower()
    for variant in {anchor, anchor.replace(" ", "")}:
        idx = original.find(variant)
        if idx < 0:
            idx = lower.find(variant.lower())
        if idx >= 0:
            start = max(0, idx - ctx)
            end = min(len(original), idx + len(variant) + ctx)
            return original[start:end].replace("\n", " ")
    return None


def detect_reversal_flags(
    item: dict[str, Any],
    original_text: str,
    triggers: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return warnings for bullets that use punchy reversal framing around numbers."""
    active_triggers = triggers or DEFAULT_REVERSAL_TRIGGERS
    candidates: list[tuple[str, int, str]] = []
    for i, bullet in enumerate(item.get("key_points") or item.get("core_views") or []):
        candidates.append(("key_points", i, str(bullet)))
    if item.get("one_line"):
        candidates.append(("one_line", 0, str(item["one_line"])))
    if item.get("summary"):
        candidates.append(("summary", 0, str(item["summary"])))

    flags = []
    for field, index, text in candidates:
        trigger = next((needle for needle in active_triggers if needle in text), None)
        if not trigger:
            continue
        numbers, proper = extract_anchors(text)
        if not numbers:
            continue
        evidence = []
        for anchor in numbers + proper:
            evidence.append(
                {
                    "anchor": anchor,
                    "context": find_in_original(anchor, original_text) or "NOT FOUND in original",
                }
            )
        flags.append(
            {
                "field": field,
                "index": index,
                "trigger": trigger,
                "text": text,
                "evidence": evidence,
                "claude_action": "Verify this framing against the raw transcript before reuse.",
            }
        )
    return flags


def summarize_one(path: Path, provider: str | None = None, model: str | None = None) -> dict[str, Any]:
    content = read_transcript(path)
    prompt = f"""Output strict JSON only. Summarize this podcast transcript for an investment research wiki.

Fields: title, speakers, channel, date, language, domain, tickers, companies, concepts, key_points, key_quotes, predictions, one_line.

Transcript file: {path.name}

---
{content}
---"""
    response = chat(
        [{"role": "system", "content": "You produce factual JSON summaries. Never invent data."}, {"role": "user", "content": prompt}],
        provider=provider,
        model=model,
    )
    data = extract_json(response)
    data["input_path"] = str(path)
    data["verification_warnings"] = detect_reversal_flags(data, content)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("-o", "--output")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    args = parser.parse_args()
    payload = {"items": [summarize_one(Path(file), args.provider, args.model) for file in args.files]}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
