"""Convert a text PDF to Markdown using pypdf.

Optional Python path for PDF -> MD ingest. It handles text PDFs. Scanned PDFs
still need OCR or a document parser such as MinerU.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a text PDF to Markdown.")
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_md", type=Path)
    args = parser.parse_args()

    try:
        from pypdf import PdfReader
    except ModuleNotFoundError:
        print(
            f"Missing dependency: pypdf. Install with `{sys.executable} -m pip install -r requirements-pdf.txt`.",
            file=sys.stderr,
        )
        return 2

    if not args.input_pdf.exists():
        print(f"Input PDF not found: {args.input_pdf}", file=sys.stderr)
        return 2

    reader = PdfReader(str(args.input_pdf))
    page_texts: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            page_texts.append(f"## Page {index}\n\n{text}")

    if not page_texts:
        print(
            "No extractable text found. This may be a scanned/image PDF; use OCR or a document parser.",
            file=sys.stderr,
        )
        return 1

    title = args.input_pdf.stem.replace("-", " ").replace("_", " ").title()
    markdown = "\n\n".join(
        [
            f"# {title}",
            f"source_pdf: {args.input_pdf.as_posix()}",
            "",
            *page_texts,
            "",
        ]
    )

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(markdown, encoding="utf-8")
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
