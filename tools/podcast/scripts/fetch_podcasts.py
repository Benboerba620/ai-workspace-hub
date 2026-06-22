#!/usr/bin/env python3
"""Scan podcast/blog/YouTube inputs and write karpathy-claude-wiki source pages."""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any

import requests
import yaml

from llm_client import LLMError, chat, extract_json
from llm_client import load_dotenv as load_llm_dotenv
from podcast_batch_summarize import detect_reversal_flags
from proxy_config import PROXY, requests_proxy


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
UA = "pod2wiki/0.1 (+https://github.com/Benboerba620/pod2wiki)"
YOUTUBE_WATCH = "https://www.youtube.com/watch?v="
YOUTUBE_RECOMMENDED_MAX_RESULTS = 5
YOUTUBE_RECOMMENDED_TOTAL_CANDIDATES = 20
YOUTUBE_RATE_LIMIT_HINT = (
    "YouTube fetching is easy to rate-limit. Keep each run small (3-5 videos), "
    "or use podcast RSS / downloaded transcripts / --input-file for bulk backfills."
)


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def is_youtube_rate_limit_error(exc: Exception | str) -> bool:
    message = str(exc).lower()
    markers = [
        "429",
        "too many requests",
        "toomanyrequests",
        "rate limit",
        "ratelimited",
        "quota",
        "temporarily blocked",
    ]
    return any(marker in message for marker in markers)


def slugify(text: str, max_len: int = 80) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", text.strip().lower(), flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-")
    return (value or "untitled")[:max_len].strip("-")


def strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text or "")
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text


def strip_markdown_light(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        line = re.sub(r"^\s*(Host|Guest|Interviewer|Speaker|主持人|嘉宾)\s*:\s*", "", line, flags=re.IGNORECASE)
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"[*_`>]+", "", cleaned)
    return cleaned.strip()


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = email.utils.parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_youtube_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_recent_youtube(value: str | None, days: int) -> bool:
    parsed = parse_youtube_date(value)
    if not parsed:
        return True
    return parsed >= datetime.now(timezone.utc) - timedelta(days=days)


def load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("config must be a YAML object")
    return data


def title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def youtube_video_id(url_or_id: str) -> str | None:
    value = (url_or_id or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return None


def run_ytdlp(args: list[str], timeout: int = 120) -> str:
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--quiet"]
    if PROXY:
        cmd.extend(["--proxy", PROXY])
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp failed")
    return result.stdout.strip()


def parse_ytdlp_json_lines(output: str, default_channel: str = "Unknown") -> list[dict[str, Any]]:
    videos = []
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_id = data.get("id")
        if not video_id:
            continue
        videos.append(
            {
                "id": video_id,
                "title": data.get("title") or "",
                "upload_date": data.get("upload_date") or "",
                "duration": data.get("duration"),
                "channel": data.get("channel") or data.get("uploader") or default_channel,
                "url": data.get("webpage_url") or f"{YOUTUBE_WATCH}{video_id}",
            }
        )
    return videos


def ytdlp_video_metadata(url_or_id: str) -> dict[str, Any] | None:
    video_id = youtube_video_id(url_or_id)
    target = f"{YOUTUBE_WATCH}{video_id}" if video_id else url_or_id
    try:
        output = run_ytdlp(["--dump-json", "--skip-download", target], timeout=120)
        return parse_ytdlp_json_lines(output)[0]
    except Exception as exc:
        eprint(f"- YouTube URL skipped: {url_or_id} ({exc})")
        if is_youtube_rate_limit_error(exc):
            eprint(f"  hint: {YOUTUBE_RATE_LIMIT_HINT}")
        if video_id:
            return {"id": video_id, "title": video_id, "upload_date": "", "duration": None, "channel": "YouTube", "url": target}
    return None


def get_channel_videos(channel_url: str, channel_name: str, max_n: int) -> list[dict[str, Any]]:
    output = run_ytdlp(
        ["--playlist-end", str(max_n), "--dump-json", "--skip-download", channel_url],
        timeout=180,
    )
    return parse_ytdlp_json_lines(output, channel_name)


def search_youtube(query: str, max_n: int) -> list[dict[str, Any]]:
    year = datetime.now().year
    output = run_ytdlp(
        ["--playlist-end", str(max_n), "--dump-json", "--skip-download", f"ytsearch{max_n}:{query} {year}"],
        timeout=150,
    )
    return parse_ytdlp_json_lines(output)


def parse_vtt(path: Path) -> str:
    lines = []
    seen = set()
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit() or line.startswith(("Kind:", "Language:")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
    return " ".join(lines)


def transcript_via_api(video_id: str, languages: list[str]) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ImportError:
        return None
    try:
        try:
            fetched = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except AttributeError:
            ytt = YouTubeTranscriptApi()
            fetched = ytt.fetch(video_id, languages=languages)
        parts = []
        for entry in fetched:
            if hasattr(entry, "text"):
                parts.append(entry.text)
            else:
                parts.append(str(entry.get("text", "")))
        return " ".join(part.strip() for part in parts if part.strip())
    except Exception as exc:
        eprint(f"- transcript API failed for {video_id}: {str(exc)[:160]}")
        if is_youtube_rate_limit_error(exc):
            eprint(f"  hint: {YOUTUBE_RATE_LIMIT_HINT}")
        return None


def transcript_via_ytdlp(video_id: str, languages: list[str]) -> str | None:
    target = f"{YOUTUBE_WATCH}{video_id}"
    with tempfile.TemporaryDirectory() as tmp:
        out_tpl = str(Path(tmp) / "%(id)s.%(ext)s")
        lang_arg = ",".join(languages)
        try:
            run_ytdlp(
                [
                    "--skip-download",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-langs",
                    lang_arg,
                    "--sub-format",
                    "vtt",
                    "-o",
                    out_tpl,
                    target,
                ],
                timeout=180,
            )
        except Exception as exc:
            eprint(f"- yt-dlp subtitles failed for {video_id}: {str(exc)[:160]}")
            if is_youtube_rate_limit_error(exc):
                eprint(f"  hint: {YOUTUBE_RATE_LIMIT_HINT}")
            return None
        candidates = sorted(Path(tmp).glob(f"{video_id}*.vtt"))
        for candidate in candidates:
            text = parse_vtt(candidate)
            if text:
                return text
    return None


def fetch_youtube_transcript(video_id: str, backend: str, languages: list[str], sleep_sec: float) -> tuple[str | None, str]:
    text = None
    status = "missing"
    if backend in {"auto", "api"}:
        text = transcript_via_api(video_id, languages)
        if text:
            status = "ok-api"
    if not text and backend in {"auto", "yt-dlp"}:
        text = transcript_via_ytdlp(video_id, languages)
        if text:
            status = "ok-ytdlp"
    if sleep_sec > 0:
        time.sleep(sleep_sec)
    return text, status


def load_history(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_history(path: Path, history: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def _whisper_settings(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("whisper") or {}
    if not isinstance(raw, dict):
        raw = {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "model": str(raw.get("model") or "tiny"),
        "clip_seconds": raw.get("clip_seconds", 600),
        "auto_threshold": int(raw.get("auto_threshold") or 1500),
    }


def _download_audio(url: str, dest: Path) -> Path:
    if dest.is_file() and dest.stat().st_size > 0:
        eprint(f"[whisper] reuse cached audio {dest} ({dest.stat().st_size / 1024 / 1024:.1f}MB)")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    eprint(f"[whisper] downloading {url} -> {dest}")
    started = time.time()
    bytes_written = 0
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": UA}, proxies=requests_proxy()) as response:
        response.raise_for_status()
        with tmp.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    fh.write(chunk)
                    bytes_written += len(chunk)
    tmp.replace(dest)
    eprint(f"[whisper] downloaded {bytes_written / 1024 / 1024:.1f}MB in {time.time() - started:.1f}s")
    return dest


def _clip_audio(src: Path, seconds: int) -> Path:
    clip = src.with_suffix(f".clip{seconds}.mp3")
    if clip.is_file() and clip.stat().st_size > 0:
        eprint(f"[whisper] reuse cached clip {clip}")
        return clip
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-t", str(int(seconds)), "-c", "copy", str(clip)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        eprint(f"[whisper] ffmpeg clip failed ({exc}); transcribing full audio")
        return src
    eprint(f"[whisper] clipped first {seconds}s -> {clip}")
    return clip


def maybe_transcribe(item: dict[str, Any], whisper_cfg: dict[str, Any], transcripts_dir: Path) -> None:
    audio_url = item.get("audio_url") or ""
    if not audio_url:
        return
    if not whisper_cfg.get("enabled", True):
        return
    description = item.get("raw_text") or ""
    threshold = int(whisper_cfg.get("auto_threshold") or 1500)
    if len(description) >= threshold:
        return
    try:
        from podcast_rss_transcribe import transcribe_audio
    except ImportError as exc:
        eprint(f"[whisper] transcription unavailable ({exc}); falling back to RSS description")
        return

    stem = f"{item.get('date')}-{slugify(item.get('channel') or 'podcast')}-{slugify(item.get('title') or 'episode')}"
    audio_ext = Path(audio_url.split("?", 1)[0]).suffix.lower() or ".mp3"
    if audio_ext not in {".mp3", ".m4a", ".aac", ".ogg", ".wav"}:
        audio_ext = ".mp3"
    audio_path = transcripts_dir / f"{stem}{audio_ext}"
    try:
        audio_path = _download_audio(audio_url, audio_path)
    except Exception as exc:
        eprint(f"[whisper] download failed for {audio_url}: {exc}; falling back to RSS description")
        return

    target = audio_path
    clip_seconds = whisper_cfg.get("clip_seconds")
    if clip_seconds:
        try:
            target = _clip_audio(audio_path, int(clip_seconds))
        except Exception as exc:
            eprint(f"[whisper] clip failed: {exc}; transcribing full audio")
            target = audio_path

    model_name = str(whisper_cfg.get("model") or "tiny")
    eprint(f"[whisper] transcribing {target.name} with {model_name} model...")
    started = time.time()
    try:
        transcript = transcribe_audio(target, model_name=model_name)
    except Exception as exc:
        eprint(f"[whisper] transcription failed: {exc}; falling back to RSS description")
        return
    elapsed = time.time() - started
    if not transcript or not transcript.strip():
        eprint(f"[whisper] empty transcript after {elapsed:.1f}s; falling back to RSS description")
        return
    eprint(f"[whisper] done in {elapsed:.1f}s, {len(transcript)} chars")
    item["raw_text"] = transcript
    item["transcribed_by"] = f"faster-whisper-{model_name}"
    item["transcript_clip_seconds"] = int(clip_seconds) if clip_seconds else None
    item["transcript_audio_path"] = str(target)


def rss_items(feed: dict[str, Any], days: int, whisper_cfg: dict[str, Any] | None = None, transcripts_dir: Path | None = None, max_items: int | None = None) -> list[dict[str, Any]]:
    url = feed.get("url") or feed.get("rss")
    if not url:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    response = requests.get(url, timeout=30, headers={"User-Agent": UA}, proxies=requests_proxy())
    response.raise_for_status()
    root = ET.fromstring(response.content)
    ns = {
        "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    channel_title = root.findtext("./channel/title") or feed.get("name") or "Unknown"
    out = []
    for item in root.findall("./channel/item"):
        if max_items is not None and len(out) >= max_items:
            break
        title = item.findtext("title") or "Untitled"
        published_raw = item.findtext("pubDate")
        published = parse_date(published_raw)
        if published and published < cutoff:
            continue
        link = item.findtext("link") or ""
        guid = item.findtext("guid") or link or title
        description = (
            item.findtext("content:encoded", namespaces=ns)
            or item.findtext("description")
            or item.findtext("itunes:summary", namespaces=ns)
            or ""
        )
        enclosure = item.find("enclosure")
        audio_url = enclosure.attrib.get("url") if enclosure is not None else ""
        record = {
            "id": guid,
            "title": strip_html(title),
            "channel": feed.get("name") or channel_title,
            "author": feed.get("author") or "",
            "date": (published or datetime.now(timezone.utc)).date().isoformat(),
            "url": link or audio_url or url,
            "audio_url": audio_url,
            "source_kind": "rss",
            "raw_text": strip_html(description),
        }
        if whisper_cfg and transcripts_dir is not None:
            maybe_transcribe(record, whisper_cfg, transcripts_dir)
        out.append(record)
    return out


def planned_inputs(config: dict[str, Any]) -> dict[str, int]:
    channels = config.get("channels") or []
    return {
        "channels": len(channels),
        "channel_rss": sum(1 for item in channels if item.get("rss")),
        "youtube_channels": sum(1 for item in channels if item.get("youtube")),
        "people_searches": len(config.get("people_searches") or []),
        "exec_searches": len(config.get("exec_searches") or []),
        "youtube_urls": len(config.get("youtube_urls") or []),
        "blog_feeds": len(config.get("blog_feeds") or []),
        "hypotheses": len(config.get("hypotheses") or {}),
    }


def collect_rss(config: dict[str, Any], days: int, history: dict[str, str], whisper_cfg: dict[str, Any] | None = None, transcripts_dir: Path | None = None, max_items_per_feed: int | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    feeds: list[dict[str, Any]] = []
    for channel in config.get("channels") or []:
        if channel.get("rss"):
            feeds.append({"name": channel.get("name"), "url": channel.get("rss"), "author": channel.get("author")})
    feeds.extend(config.get("blog_feeds") or [])
    for feed in feeds:
        try:
            for item in rss_items(feed, days, whisper_cfg=whisper_cfg, transcripts_dir=transcripts_dir, max_items=max_items_per_feed):
                key = item["id"]
                if key not in history:
                    items.append(item)
        except Exception as exc:
            eprint(f"- feed skipped: {feed.get('name') or feed.get('url')} ({exc})")
    return items


def collect_youtube(
    config: dict[str, Any],
    days: int,
    history: dict[str, str],
    youtube_mode: str,
    max_results: int,
    transcript_backend: str,
    transcript_languages: list[str],
    transcript_sleep: float,
    explicit_urls: list[str],
    explicit_queries: list[str],
) -> list[dict[str, Any]]:
    videos: list[dict[str, Any]] = []
    channels = config.get("channels") or []
    youtube_sources = 0
    if youtube_mode in {"channels", "all"}:
        youtube_sources += sum(1 for channel in channels if channel.get("youtube"))
    if youtube_mode in {"search", "all"}:
        queries = explicit_queries or (list(config.get("people_searches") or []) + list(config.get("exec_searches") or []))
        youtube_sources += len(queries)
    if youtube_mode in {"urls", "all"}:
        youtube_sources += len(list(config.get("youtube_urls") or []) + explicit_urls)
    if youtube_sources:
        planned_candidates = youtube_sources * max_results
        eprint(f"Note: {YOUTUBE_RATE_LIMIT_HINT}")
        if max_results > YOUTUBE_RECOMMENDED_MAX_RESULTS or planned_candidates > YOUTUBE_RECOMMENDED_TOTAL_CANDIDATES:
            eprint(
                f"Warning: this run may check up to about {planned_candidates} YouTube candidates "
                f"({youtube_sources} sources x {max_results}). For large backfills, prefer RSS or local transcripts."
            )
    if youtube_mode in {"channels", "all"}:
        for channel in channels:
            if not channel.get("youtube"):
                continue
            try:
                videos.extend(get_channel_videos(channel["youtube"], channel.get("name") or "YouTube", max_results))
            except Exception as exc:
                eprint(f"- YouTube channel skipped: {channel.get('name') or channel.get('youtube')} ({exc})")
                if is_youtube_rate_limit_error(exc):
                    eprint(f"  hint: {YOUTUBE_RATE_LIMIT_HINT}")

    if youtube_mode in {"search", "all"}:
        queries = explicit_queries or (list(config.get("people_searches") or []) + list(config.get("exec_searches") or []))
        for query in queries:
            try:
                for video in search_youtube(str(query), max_results):
                    video["search_query"] = str(query)
                    videos.append(video)
            except Exception as exc:
                eprint(f"- YouTube search skipped: {query} ({exc})")
                if is_youtube_rate_limit_error(exc):
                    eprint(f"  hint: {YOUTUBE_RATE_LIMIT_HINT}")

    if youtube_mode in {"urls", "all"}:
        url_values = list(config.get("youtube_urls") or []) + explicit_urls
        for value in url_values:
            if isinstance(value, dict):
                raw_url = value.get("url") or value.get("youtube") or ""
            else:
                raw_url = str(value)
            meta = ytdlp_video_metadata(raw_url)
            if meta:
                videos.append(meta)

    items: list[dict[str, Any]] = []
    seen_video_ids = set()
    for video in videos:
        video_id = video.get("id")
        if not video_id or video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)
        if not is_recent_youtube(video.get("upload_date"), days):
            continue
        history_key = f"youtube:{video_id}"
        if history_key in history:
            continue
        text, transcript_status = fetch_youtube_transcript(video_id, transcript_backend, transcript_languages, transcript_sleep)
        if not text:
            eprint(f"- YouTube transcript missing: {video.get('title') or video_id} ({transcript_status})")
            continue
        published = parse_youtube_date(video.get("upload_date"))
        item_date = (published or datetime.now(timezone.utc)).date().isoformat()
        items.append(
            {
                "id": history_key,
                "title": video.get("title") or video_id,
                "channel": video.get("channel") or "YouTube",
                "author": "",
                "date": item_date,
                "url": video.get("url") or f"{YOUTUBE_WATCH}{video_id}",
                "audio_url": "",
                "source_kind": "youtube",
                "raw_text": text,
                "duration_sec": video.get("duration"),
                "search_query": video.get("search_query", ""),
                "transcript_status": transcript_status,
            }
        )
    return items


def collect(
    config: dict[str, Any],
    days: int,
    history: dict[str, str],
    mode: str,
    youtube_mode: str,
    youtube_max_results: int,
    transcript_backend: str,
    transcript_languages: list[str],
    transcript_sleep: float,
    youtube_urls: list[str],
    youtube_queries: list[str],
    whisper_cfg: dict[str, Any] | None = None,
    transcripts_dir: Path | None = None,
    max_items_per_feed: int | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if mode in {"all", "rss"}:
        items.extend(collect_rss(config, days, history, whisper_cfg=whisper_cfg, transcripts_dir=transcripts_dir, max_items_per_feed=max_items_per_feed))
    if mode in {"all", "youtube"}:
        items.extend(
            collect_youtube(
                config,
                days,
                history,
                youtube_mode,
                youtube_max_results,
                transcript_backend,
                transcript_languages,
                transcript_sleep,
                youtube_urls,
                youtube_queries,
            )
        )
    return items


def file_item(path: Path, title: str | None, channel: str | None, source_url: str | None, date: str | None) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    item_date = date or datetime.now().date().isoformat()
    item_title = title or title_from_markdown(text, path.stem)
    return {
        "id": f"file:{path.resolve()}:{path.stat().st_mtime_ns}",
        "title": item_title,
        "channel": channel or "Local File",
        "author": "",
        "date": item_date,
        "url": source_url or str(path),
        "audio_url": "",
        "source_kind": "file",
        "raw_text": text,
    }


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9+.-]{2,}", text)
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "was",
        "were",
        "have",
        "has",
        "you",
        "your",
        "host",
        "guest",
        "speaker",
        "interviewer",
        "podcast",
        "transcript",
    }
    counts: dict[str, int] = {}
    for word in words:
        key = word.strip()
        if key.lower() in stop:
            continue
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].lower()))
    return [word for word, _count in ranked[:limit]]


def summarize_without_llm(item: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    text = item.get("raw_text") or ""
    plain = strip_html(strip_markdown_light(text))
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", plain) if p.strip()]
    first = paragraphs[0] if paragraphs else plain[:500]
    if len(first) > 700:
        first = first[:700].rsplit(" ", 1)[0] + "..."
    keywords = extract_keywords(plain)
    hypotheses = config.get("hypotheses") or {}
    h_links = []
    lower = plain.lower()
    for hid, hdata in hypotheses.items():
        for keyword in hdata.get("keywords") or []:
            if str(keyword).lower() in lower:
                h_links.append({"hypothesis": hid, "direction": "neutral", "reason": f"matched keyword: {keyword}"})
                break
    data = {
        "summary": first or "No summary generated. Review the raw text.",
        "core_views": [f"Keyword: {kw}" for kw in keywords[:6]],
        "key_data": [],
        "related_tickers": [],
        "related_concepts": [],
        "predictions": [],
        "h_links": h_links,
        "speakers": [],
        "key_quotes": [],
        "confidence": "low",
    }
    data["verification_warnings"] = detect_reversal_flags(
        {"key_points": data["core_views"], "one_line": data["summary"]},
        text,
        triggers=config.get("reversal_triggers"),
    )
    return data


def summarize_item(item: dict[str, Any], config: dict[str, Any], locale: str, no_llm: bool = False) -> dict[str, Any]:
    if no_llm:
        return summarize_without_llm(item, config)
    text = item.get("raw_text") or ""
    max_chars = int(config.get("max_transcript_chars") or 15000)
    if len(text) > max_chars:
        text = text[: int(max_chars * 0.75)] + "\n\n[... omitted ...]\n\n" + text[-int(max_chars * 0.2) :]
    hypotheses = config.get("hypotheses") or {}
    system = "You summarize podcasts and long-form research articles for an investment knowledge base. Output strict JSON only."
    user = f"""Summarize this source for a karpathy-claude-wiki compatible source-summary page.

Language preference: {locale}

Return JSON with keys:
summary, core_views, key_data, related_tickers, related_concepts, predictions, h_links, speakers, key_quotes.

Hypotheses:
{json.dumps(hypotheses, ensure_ascii=False, indent=2)}

Metadata:
title={item.get('title')}
channel={item.get('channel')}
url={item.get('url')}
date={item.get('date')}

Source text:
---
{text}
---"""
    llm_cfg = config.get("llm") or {}
    content = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        provider=llm_cfg.get("provider"),
        model=llm_cfg.get("model"),
        max_tokens=int(llm_cfg.get("max_tokens") or 4096),
    )
    data = extract_json(content)
    data["verification_warnings"] = detect_reversal_flags(
        {
            "key_points": data.get("core_views") or data.get("key_points") or [],
            "one_line": data.get("summary") or "",
        },
        text,
        triggers=config.get("reversal_triggers"),
    )
    return data


def split_text(text: str, max_chars: int) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[i : i + max_chars])
            continue
        if len(current) + len(paragraph) + 2 > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = paragraph if not current else current + "\n\n" + paragraph
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def translate_full_text(item: dict[str, Any], config: dict[str, Any], target_locale: str, max_chars: int = 6000) -> str:
    text = item.get("raw_text") or ""
    chunks = split_text(text, max_chars)
    llm_cfg = config.get("llm") or {}
    translated = []
    for index, chunk in enumerate(chunks, 1):
        prompt = f"""Translate the following podcast/article transcript into {target_locale}.

Rules:
- Preserve names, company names, ticker symbols, numbers, URLs, and units.
- Keep paragraph structure.
- Do not summarize. Translate the full text.
- If a term is technical, keep the English term and add a short Chinese explanation on first use when target is Chinese.

Chunk {index}/{len(chunks)}:
---
{chunk}
---"""
        translated.append(
            chat(
                [
                    {"role": "system", "content": "You are a careful transcript translator. Do not add commentary."},
                    {"role": "user", "content": prompt},
                ],
                provider=llm_cfg.get("provider"),
                model=llm_cfg.get("model"),
                max_tokens=int(llm_cfg.get("translation_max_tokens") or llm_cfg.get("max_tokens") or 4096),
                temperature=0.1,
                timeout=180,
            )
        )
    return "\n\n".join(translated)


def write_raw(item: dict[str, Any], base: Path) -> Path:
    raw_dir = base / "raw" / "podcasts"
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{item['date']}-{slugify(item['channel'])}-{slugify(item['title'])}.md"
    path = raw_dir / filename
    transcribed_by = item.get("transcribed_by")
    transcribed_line = f"transcribed_by: {transcribed_by}\n" if transcribed_by else ""
    clip_secs = item.get("transcript_clip_seconds")
    clip_line = f"transcript_clip_seconds: {clip_secs}\n" if clip_secs else ""
    body = f"""---
title: {json.dumps(item['title'], ensure_ascii=False)}
type: raw-transcript
source: {json.dumps(item.get('url') or '', ensure_ascii=False)}
created: {item['date']}
{transcribed_line}{clip_line}---

# {item['title']}

Channel: {item.get('channel') or ''}

URL: {item.get('url') or ''}

Audio: {item.get('audio_url') or ''}

## Raw Text

{item.get('raw_text') or ''}
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_translation(item: dict[str, Any], translated_text: str, base: Path, locale: str) -> Path:
    translation_dir = base / "translations"
    translation_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{item['date']}-{slugify(item['channel'])}-{slugify(item['title'])}-{slugify(locale, 12)}.md"
    path = translation_dir / filename
    body = f"""---
title: {json.dumps(item['title'], ensure_ascii=False)}
type: full-translation
source: {json.dumps(item.get('url') or '', ensure_ascii=False)}
created: {item['date']}
language: {locale}
---

# {item['title']}

Source: {item.get('url') or ''}

{translated_text}
"""
    path.write_text(body, encoding="utf-8")
    return path


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(json.dumps(v, ensure_ascii=False) for v in values) + "]"


def write_source(item: dict[str, Any], structured: dict[str, Any], source_dir: Path, raw_ref: str, domain: str, locale: str) -> Path:
    source_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{item['date']}-{slugify(item['channel'])}-{slugify(item['title'])}.md"
    related = []
    for ticker in structured.get("related_tickers") or []:
        related.append(f"[[{ticker}]]")
    for concept in structured.get("related_concepts") or []:
        related.append(f"[[{concept}]]")
    path = source_dir / filename
    key_data = structured.get("key_data") or []
    predictions = structured.get("predictions") or []
    quotes = structured.get("key_quotes") or structured.get("quotes") or []
    h_links = structured.get("h_links") or []
    transcribed_by = item.get("transcribed_by")
    transcribed_line = f"transcribed_by: {transcribed_by}\n" if transcribed_by else ""
    body = f"""---
title: {json.dumps(item['title'], ensure_ascii=False)}
type: source-summary
domain: {domain}
sources: [{json.dumps(raw_ref, ensure_ascii=False)}]
related: {yaml_list(related)}
created: {item['date']}
updated: {datetime.now().date().isoformat()}
confidence: {structured.get('confidence') or 'medium'}
speakers: {yaml_list(structured.get('speakers') or [])}
language: {locale}
{transcribed_line}---

## TL;DR / 一句话摘要

{structured.get('summary') or ''}

## Key Data / 关键数据

{format_bullets(key_data)}

## Direct Quotes / 原始引文

{format_bullets(quotes)}

## Implications / 启示

{format_bullets(structured.get('core_views') or structured.get('key_points') or [])}

## Verifiable Predictions / 可验证预测

{format_bullets(predictions)}

## Hypothesis Links / 假设关联

{format_bullets(h_links)}

## Verification Warnings / 待核查红灯

{format_bullets(structured.get('verification_warnings') or [])}
"""
    path.write_text(body, encoding="utf-8")
    return path


def item_log_block(item: dict[str, Any], structured: dict[str, Any], source_paths: list[str], translation_paths: list[str]) -> str:
    source_line = ", ".join(f"`{path}`" for path in source_paths) if source_paths else "None"
    translation_line = ", ".join(f"`{path}`" for path in translation_paths) if translation_paths else "None"
    views = structured.get("core_views") or structured.get("key_points") or []
    warnings = structured.get("verification_warnings") or []
    return textwrap.dedent(
        f"""
        ### {item.get('title') or 'Untitled'}

        📺 {item.get('channel') or item.get('source_kind') or 'Unknown'} | 📅 {item.get('date') or ''} | 🔗 {item.get('url') or ''}

        **TL;DR**: {structured.get('summary') or ''}

        **Key Points**
        {format_bullets(views)}

        **Source Pages**: {source_line}

        **Translations**: {translation_line}

        **Verification Warnings**
        {format_bullets(warnings)}
        """
    ).strip()


def fallback_report(processed: list[dict[str, Any]], days: int) -> str:
    blocks = [
        f"# pod2wiki Insight Log\n\n扫描窗口：最近 {days} 天\n\n找到 {len(processed)} 条内容。",
    ]
    for entry in processed:
        blocks.append(item_log_block(entry["item"], entry["structured"], entry["source_pages"], entry["translation_pages"]))
    return "\n\n".join(blocks)


def generate_insight_report(processed: list[dict[str, Any]], config: dict[str, Any], days: int, no_llm: bool) -> str:
    if no_llm:
        return fallback_report(processed, days)
    compact = []
    for entry in processed:
        item = entry["item"]
        structured = entry["structured"]
        compact.append(
            {
                "title": item.get("title"),
                "channel": item.get("channel"),
                "date": item.get("date"),
                "url": item.get("url"),
                "summary": structured.get("summary"),
                "core_views": structured.get("core_views") or structured.get("key_points") or [],
                "key_data": structured.get("key_data") or [],
                "predictions": structured.get("predictions") or [],
                "h_links": structured.get("h_links") or [],
                "verification_warnings": structured.get("verification_warnings") or [],
            }
        )
    llm_cfg = config.get("llm") or {}
    prompt = f"""Write a Chinese professional investor insight log from these podcast/article summaries.

Structure:
# pod2wiki Insight Log
## 本次主线
## 内容逐条整理
## 假设影响
## 待核查红灯

Rules:
- Separate facts from interpretation.
- Mention verification warnings explicitly.
- Do not invent data not present in JSON.

Days: {days}
JSON:
{json.dumps(compact, ensure_ascii=False, indent=2)}
"""
    return chat(
        [
            {"role": "system", "content": "You write concise Chinese investment research logs from structured source data."},
            {"role": "user", "content": prompt},
        ],
        provider=llm_cfg.get("provider"),
        model=llm_cfg.get("model"),
        max_tokens=int(llm_cfg.get("report_max_tokens") or 6000),
        temperature=0.2,
        timeout=180,
    )


def append_insight_log(path: Path, report: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = "# AI 行业洞见追踪日志\n\n---\n\n" if not path.exists() else "\n\n---\n\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{header}## {timestamp} 扫描\n\n{report.strip()}\n")


def format_bullets(items: Any) -> str:
    if not items:
        return "- None"
    lines = []
    for item in items:
        if isinstance(item, dict):
            lines.append("- " + "; ".join(f"{k}: {v}" for k, v in item.items()))
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--env-file", help="Optional .env file to load before LLM calls.")
    parser.add_argument("--output-dir", help="Runtime output directory. Defaults to ./output in the pod2wiki project.")
    parser.add_argument("--days", type=int)
    parser.add_argument("--wiki-out")
    parser.add_argument("--domain", default="investing")
    parser.add_argument("--locale", default="zh-CN")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--days-quick", action="store_true")
    parser.add_argument("--input-file", action="append", default=[], help="Local transcript/article Markdown or text file. Can be passed multiple times.")
    parser.add_argument("--title", help="Title override for a single --input-file run.")
    parser.add_argument("--channel", help="Channel/source label override for local files.")
    parser.add_argument("--source-url", help="Original URL override for a single --input-file run.")
    parser.add_argument("--date", help="YYYY-MM-DD override for local files.")
    parser.add_argument("--no-llm", action="store_true", help="Write an extractive low-confidence source page without calling an LLM.")
    parser.add_argument("--max-items", type=int, help="Global limit on items to summarize/write after collection.")
    parser.add_argument("--max-items-per-feed", type=int, help="Limit RSS/blog items collected from each feed. Defaults to config max_items_per_feed.")
    parser.add_argument("--mode", choices=["all", "rss", "youtube"], default="all", help="Discovery mode when --input-file is not used.")
    parser.add_argument("--youtube-mode", choices=["channels", "search", "urls", "all"], default="all", help="YouTube discovery mode.")
    parser.add_argument("--youtube-url", action="append", default=[], help="Explicit YouTube URL or video id. Can be passed multiple times.")
    parser.add_argument("--youtube-query", action="append", default=[], help="Explicit YouTube search query. Can be passed multiple times.")
    parser.add_argument("--youtube-max-results", type=int, help="Max YouTube videos per channel/search query. Defaults to config max_videos_per_channel.")
    parser.add_argument("--transcript-backend", choices=["auto", "api", "yt-dlp"], default="auto")
    parser.add_argument("--transcript-languages", default="en,en-US,en-GB,zh-Hans,zh", help="Comma-separated subtitle language preference.")
    parser.add_argument("--transcript-sleep", type=float, default=1.5, help="Sleep seconds between transcript requests.")
    parser.add_argument("--whisper-model", choices=["tiny", "base", "small", "medium", "large-v3"], help="Override whisper.model for podcast MP3 transcription.")
    parser.add_argument("--whisper-clip-seconds", type=int, help="Override whisper.clip_seconds: transcribe only first N seconds (use 0 for full episode).")
    parser.add_argument("--no-whisper", action="store_true", help="Disable Whisper transcription; use raw RSS description instead.")
    parser.add_argument("--whisper-threshold", type=int, help="Override whisper.auto_threshold: auto-transcribe when RSS description shorter than N chars.")
    parser.add_argument("--translate-full", action="store_true", help="Translate full raw text/transcript with the configured LLM.")
    parser.add_argument("--translation-locale", default="zh-CN")
    parser.add_argument("--write-insight-log", action="store_true", help="Append a run-level insight report.")
    parser.add_argument("--insight-log", help="Insight log path. Defaults to <output-dir>/ai-insights-log.md.")
    args = parser.parse_args()

    global OUTPUT
    if args.output_dir:
        OUTPUT = Path(args.output_dir)
    config_path = Path(args.config)
    if args.env_file:
        load_llm_dotenv(Path(args.env_file))
    config = load_config(config_path)
    days = 1 if args.days_quick else (args.days or int(config.get("days_lookback") or 7))
    youtube_max_results = args.youtube_max_results
    if youtube_max_results is None:
        youtube_max_results = int(config.get("max_videos_per_channel") or 3)
    max_items_per_feed = args.max_items_per_feed
    if max_items_per_feed is None and config.get("max_items_per_feed") is not None:
        max_items_per_feed = int(config.get("max_items_per_feed") or 0) or None

    if args.dry_run:
        payload = {
            "ok": True,
            "mode": "dry-run",
            "config": str(config_path),
            "days": days,
            "planned_inputs": planned_inputs(config),
            "input_files": len(args.input_file),
            "discovery_mode": args.mode,
            "youtube_mode": args.youtube_mode,
            "youtube_max_results": youtube_max_results,
            "max_items": args.max_items,
            "max_items_per_feed": max_items_per_feed,
            "wiki_out": args.wiki_out,
            "note": "dry-run validates config and does not call network, LLM, or write files",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        eprint(f"Dry-run OK: {payload['planned_inputs']}")
        return 0

    history_path = OUTPUT / "seen_history.json"
    history = load_history(history_path)

    whisper_cfg = _whisper_settings(config)
    if args.no_whisper:
        whisper_cfg["enabled"] = False
    if args.whisper_model:
        whisper_cfg["model"] = args.whisper_model
    if args.whisper_clip_seconds is not None:
        whisper_cfg["clip_seconds"] = args.whisper_clip_seconds if args.whisper_clip_seconds > 0 else None
    if args.whisper_threshold is not None:
        whisper_cfg["auto_threshold"] = args.whisper_threshold
    transcripts_dir = OUTPUT / "transcripts"

    items = []
    for input_file in args.input_file:
        items.append(file_item(Path(input_file), args.title, args.channel, args.source_url, args.date))
    if not args.input_file:
        items = collect(
            config,
            days,
            history,
            args.mode,
            args.youtube_mode,
            youtube_max_results,
            args.transcript_backend,
            [part.strip() for part in args.transcript_languages.split(",") if part.strip()],
            args.transcript_sleep,
            args.youtube_url,
            args.youtube_query,
            whisper_cfg=whisper_cfg,
            transcripts_dir=transcripts_dir,
            max_items_per_feed=max_items_per_feed,
        )
    if args.max_items is not None:
        items = items[: args.max_items]
    source_pages: list[str] = []
    raw_pages: list[str] = []
    translation_pages: list[str] = []
    warnings: list[dict[str, Any]] = []
    processed: list[dict[str, Any]] = []
    local_source_dir = OUTPUT / "sources"

    if args.wiki_out:
        wiki_source_dir = Path(args.wiki_out)
        wiki_root = wiki_source_dir.parent
    else:
        wiki_source_dir = None
        wiki_root = OUTPUT

    for item in items:
        if not item.get("raw_text"):
            continue
        try:
            structured = summarize_item(item, config, args.locale, no_llm=args.no_llm)
        except (LLMError, json.JSONDecodeError) as exc:
            eprint(f"- LLM skipped: {item.get('title')} ({exc})")
            continue
        raw_path = write_raw(item, wiki_root)
        raw_ref = str(raw_path.relative_to(wiki_root)).replace("\\", "/")
        local_raw_copy = write_raw(item, OUTPUT)
        local_source = write_source(item, structured, local_source_dir, raw_ref, args.domain, args.locale)
        item_translation_pages: list[str] = []
        raw_pages.append(str(local_raw_copy))
        if wiki_source_dir:
            raw_pages.append(str(raw_path))
        source_pages.append(str(local_source))
        if wiki_source_dir:
            wiki_source = write_source(item, structured, wiki_source_dir, raw_ref, args.domain, args.locale)
            source_pages.append(str(wiki_source))
        if args.translate_full and not args.no_llm:
            try:
                translated_text = translate_full_text(item, config, args.translation_locale)
                local_translation = write_translation(item, translated_text, OUTPUT, args.translation_locale)
                translation_pages.append(str(local_translation))
                item_translation_pages.append(str(local_translation))
                if wiki_source_dir:
                    wiki_translation = write_translation(item, translated_text, wiki_root, args.translation_locale)
                    translation_pages.append(str(wiki_translation))
                    item_translation_pages.append(str(wiki_translation))
            except LLMError as exc:
                eprint(f"- translation skipped: {item.get('title')} ({exc})")
        warnings.extend(structured.get("verification_warnings") or [])
        processed.append(
            {
                "item": item,
                "structured": structured,
                "source_pages": [str(local_source)],
                "translation_pages": item_translation_pages,
            }
        )
        if item.get("source_kind") != "file":
            history[item["id"]] = datetime.now(timezone.utc).isoformat()

    save_history(history_path, history)
    insight_log_path = None
    if args.write_insight_log and processed:
        try:
            report = generate_insight_report(processed, config, days, args.no_llm)
            target = Path(args.insight_log) if args.insight_log else OUTPUT / "ai-insights-log.md"
            if not target.is_absolute():
                target = Path.cwd() / target
            append_insight_log(target, report)
            insight_log_path = str(target)
        except LLMError as exc:
            eprint(f"- insight log skipped: {exc}")
    payload = {
        "ok": True,
        "items_found": len(items),
        "items_summarized": len(processed),
        "source_pages_count": len(source_pages),
        "source_pages_written": source_pages,
        "raw_pages_written": raw_pages,
        "translation_pages_written": translation_pages,
        "insight_log": insight_log_path,
        "verification_warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    eprint(textwrap.dedent(f"""
    pod2wiki complete
    - found: {len(items)}
    - source pages written: {len(source_pages)}
    - verification warnings: {len(warnings)}
    """).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
