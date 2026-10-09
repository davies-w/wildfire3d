#!/usr/bin/env python3
"""Search the FDS / Smokeview PDF manuals for a term and print context.

Usage:
    pdfgrep.py <pdf> <term> [window_chars] [max_hits]
"""

from __future__ import annotations

import re
import sys

from pypdf import PdfReader


def main() -> None:
    pdf = sys.argv[1]
    term = sys.argv[2]
    window = int(sys.argv[3]) if len(sys.argv) > 3 else 700
    max_hits = int(sys.argv[4]) if len(sys.argv) > 4 else 6

    reader = PdfReader(pdf)
    print(f"{pdf}: {len(reader.pages)} pages, searching for {term!r}\n")

    hits = 0
    for pno, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        if term.lower() not in text.lower():
            continue
        for m in re.finditer(re.escape(term.lower()), text.lower()):
            start = max(0, m.start() - window // 3)
            end = min(len(text), m.end() + window)
            snippet = re.sub(r"\s+", " ", text[start:end])
            print(f"--- page {pno + 1} ---")
            print(snippet)
            print()
            hits += 1
            if hits >= max_hits:
                return
            break


if __name__ == "__main__":
    main()
