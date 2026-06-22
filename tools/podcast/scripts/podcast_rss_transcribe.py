#!/usr/bin/env python3
"""Download a podcast MP3 and transcribe it with optional faster-whisper."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import requests

from proxy_config import requests_proxy


def slugify(text: str, max_len: int = 80) -> str:
    value = re.sub(r"[^\w.-]+", "-", text.strip().lower())
    return re.sub(r"-+", "-", value).strip("-")[:max_len] or "podcast"


def download_mp3(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120, proxies=requests_proxy()) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
    return dest


def probe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        return None
    return None


def transcribe_audio(path: Path, model_name: str = "medium", language: str = "en") -> str:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise RuntimeError('MP3 transcription requires: pip install "faster-whisper"') from exc
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, _info = model.transcribe(str(path), language=language)
    return "\n".join(segment.text.strip() for segment in segments if segment.text.strip())


def write_transcript(path: Path, title: str, channel: str, date: str, source_url: str, audio_url: str, body: str, model: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(Path(audio_url)) if Path(audio_url).is_file() else None
    text = f"""---
title: {title}
type: raw-transcript
channel: {channel}
created: {date}
source: {source_url}
audio: {audio_url}
model: {model}
duration_sec: {duration or ''}
---

# {title}

{body}
"""
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="MP3 URL")
    parser.add_argument("--title", required=True)
    parser.add_argument("--channel", default="Unknown")
    parser.add_argument("--date", required=True)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--model", default="medium")
    parser.add_argument("--language", default="en")
    parser.add_argument("--out-dir", default="output/transcripts")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    stem = f"{args.date}-{slugify(args.channel)}-{slugify(args.title)}"
    mp3 = download_mp3(args.url, out_dir / f"{stem}.mp3")
    transcript = transcribe_audio(mp3, args.model, args.language)
    out_path = write_transcript(out_dir / f"{stem}.md", args.title, args.channel, args.date, args.source_url, args.url, transcript, args.model)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
