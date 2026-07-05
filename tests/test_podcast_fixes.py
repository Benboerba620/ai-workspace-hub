"""Regression tests for the tools/podcast bug-fix batch.

Covers:
1. llm_client provider/model precedence (explicit arg > env > default)
2. parse_date resilience + per-item RSS error isolation + Atom support
8. extract_json rejects non-object JSON with LLMError
9. podcast_rss_transcribe YAML frontmatter escaping
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

import fetch_podcasts
import llm_client
import podcast_rss_transcribe


# ---------------------------------------------------------------------------
# Fix 1: provider/model precedence
# ---------------------------------------------------------------------------

LLM_ENV_KEYS = [
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "KIMI_API_KEY",
    "KIMI_BASE_URL",
    "KIMI_MODEL",
]


@pytest.fixture
def llm_env(monkeypatch):
    # env_value() treats "" as unset; setting all keys also blocks any stray
    # local .env file from leaking values through load_dotenv's setdefault.
    for key in LLM_ENV_KEYS:
        monkeypatch.setenv(key, "")
    return monkeypatch


def test_explicit_provider_beats_env(llm_env):
    llm_env.setenv("LLM_PROVIDER", "deepseek")
    llm_env.setenv("LLM_API_KEY", "sk-generic-deepseek")
    llm_env.setenv("LLM_MODEL", "deepseek-v4-flash")
    llm_env.setenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_env.setenv("KIMI_API_KEY", "sk-kimi-real")

    resolved = llm_client.resolve_provider(provider="kimi")
    assert resolved["provider"] == "kimi"
    # Generic LLM_* values belong to the deepseek block and must not leak.
    assert resolved["api_key"] == "sk-kimi-real"
    assert resolved["model"] == "moonshot-v1-128k"
    assert resolved["base_url"] == "https://api.moonshot.cn/v1"


def test_env_provider_used_when_arg_is_none(llm_env):
    llm_env.setenv("LLM_PROVIDER", "kimi")
    llm_env.setenv("KIMI_API_KEY", "sk-kimi")
    # provider=None simulates argparse defaults / missing config keys.
    resolved = llm_client.resolve_provider(provider=None, model=None)
    assert resolved["provider"] == "kimi"
    assert resolved["api_key"] == "sk-kimi"


def test_explicit_model_beats_env_model(llm_env):
    llm_env.setenv("LLM_PROVIDER", "deepseek")
    llm_env.setenv("LLM_API_KEY", "sk-x")
    llm_env.setenv("LLM_MODEL", "env-model")
    resolved = llm_client.resolve_provider(model="cli-model")
    assert resolved["model"] == "cli-model"


def test_env_model_still_applies_without_explicit_model(llm_env):
    llm_env.setenv("LLM_PROVIDER", "deepseek")
    llm_env.setenv("LLM_API_KEY", "sk-x")
    llm_env.setenv("LLM_MODEL", "env-model")
    resolved = llm_client.resolve_provider()
    assert resolved["model"] == "env-model"


def test_default_provider_when_nothing_set(llm_env):
    llm_env.setenv("DEEPSEEK_API_KEY", "sk-ds")
    resolved = llm_client.resolve_provider()
    assert resolved["provider"] == "deepseek"
    assert resolved["model"] == "deepseek-v4-flash"


# ---------------------------------------------------------------------------
# Fix 2: date parsing + per-item resilience + Atom
# ---------------------------------------------------------------------------

def test_parse_date_invalid_returns_none():
    assert fetch_podcasts.parse_date("definitely not a date") is None
    assert fetch_podcasts.parse_date("") is None
    assert fetch_podcasts.parse_date(None) is None


def test_parse_date_valid_is_tz_aware():
    parsed = fetch_podcasts.parse_date("Tue, 01 Jul 2025 10:00:00 GMT")
    assert parsed is not None
    assert parsed.tzinfo is not None


def test_parse_iso_date():
    parsed = fetch_podcasts.parse_iso_date("2025-07-01T10:00:00Z")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert fetch_podcasts.parse_iso_date("garbage") is None
    assert fetch_podcasts.parse_iso_date(None) is None


RSS_XML = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>Test Feed</title>
<item><title>Good Item</title><pubDate>Tue, 01 Jul 2025 10:00:00 GMT</pubDate>
<link>https://example.com/1</link><guid>g1</guid><description>desc one</description></item>
<item><title>Bad Date Item</title><pubDate>not-a-date</pubDate>
<link>https://example.com/2</link><guid>g2</guid><description>desc two</description>
<enclosure url="https://example.com/2.mp3" type="audio/mpeg"/></item>
</channel></rss>"""


def test_bad_pubdate_does_not_kill_feed():
    root = ET.fromstring(RSS_XML)
    entries = fetch_podcasts._rss_entries(root, "test-feed")
    assert [entry["guid"] for entry in entries] == ["g1", "g2"]
    assert entries[0]["published"] is not None
    assert entries[1]["published"] is None  # bad date degrades, item survives
    assert entries[1]["audio_url"] == "https://example.com/2.mp3"


class _FakeResponse:
    def __init__(self, text: str):
        self.content = text.encode("utf-8")

    def raise_for_status(self) -> None:
        pass


def test_rss_items_dedupes_history_before_transcription(monkeypatch):
    monkeypatch.setattr(fetch_podcasts.requests, "get", lambda *a, **k: _FakeResponse(RSS_XML))
    transcribed = []
    monkeypatch.setattr(
        fetch_podcasts, "maybe_transcribe", lambda item, cfg, d: transcribed.append(item["id"])
    )
    items = fetch_podcasts.rss_items(
        {"name": "T", "url": "http://feed.example"},
        days=100000,
        whisper_cfg={"enabled": True},
        transcripts_dir=Path("."),
        history={"g1": "2026-01-01"},
    )
    assert [item["id"] for item in items] == ["g2"]
    # The already-seen item must never reach the download/transcription step.
    assert transcribed == ["g2"]


ATOM_XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Atom Blog</title>
<entry><title>Post One</title><id>atom-1</id>
<published>2025-07-01T00:00:00Z</published>
<link rel="alternate" href="https://blog.example/1"/>
<summary>hello atom world</summary></entry>
<entry><title>Post Two</title><id>atom-2</id>
<updated>2025-07-02T00:00:00+00:00</updated>
<link href="https://blog.example/2"/>
<content type="html">&lt;p&gt;rich content&lt;/p&gt;</content></entry>
</feed>"""


def test_rss_items_supports_atom_feeds(monkeypatch):
    monkeypatch.setattr(fetch_podcasts.requests, "get", lambda *a, **k: _FakeResponse(ATOM_XML))
    items = fetch_podcasts.rss_items({"name": "Blog", "url": "http://feed.example"}, days=100000)
    assert [item["id"] for item in items] == ["atom-1", "atom-2"]
    assert items[0]["url"] == "https://blog.example/1"
    assert items[0]["raw_text"] == "hello atom world"
    assert items[1]["url"] == "https://blog.example/2"  # rel-less link accepted
    assert "rich content" in items[1]["raw_text"]
    assert items[0]["date"] == "2025-07-01"


# ---------------------------------------------------------------------------
# Fix 8: extract_json object guard
# ---------------------------------------------------------------------------

def test_extract_json_plain_object():
    assert llm_client.extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced_object():
    assert llm_client.extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_object_embedded_in_text():
    assert llm_client.extract_json('Here you go: {"a": 1} hope that helps') == {"a": 1}


def test_extract_json_top_level_array_raises_llmerror():
    with pytest.raises(llm_client.LLMError):
        llm_client.extract_json('[{"a": 1}]')


def test_extract_json_scalar_raises_llmerror():
    with pytest.raises(llm_client.LLMError):
        llm_client.extract_json("42")


# ---------------------------------------------------------------------------
# Fix 9: YAML frontmatter escaping in podcast_rss_transcribe
# ---------------------------------------------------------------------------

def test_write_transcript_frontmatter_survives_special_chars(tmp_path):
    title = 'EP42: "AI" 拐点 — a: b'
    channel = "Chan: nel [x]"
    path = podcast_rss_transcribe.write_transcript(
        tmp_path / "t.md",
        title=title,
        channel=channel,
        date="2026-07-05",
        source_url="https://example.com/ep?x=1&y=2",
        audio_url="",
        body="body text",
        model="tiny",
    )
    text = path.read_text(encoding="utf-8")
    frontmatter = text.split("---")[1]
    data = yaml.safe_load(frontmatter)
    assert data["title"] == title
    assert data["channel"] == channel
    assert data["source"] == "https://example.com/ep?x=1&y=2"
    assert data["type"] == "raw-transcript"
