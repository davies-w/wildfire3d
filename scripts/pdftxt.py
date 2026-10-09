"""Dump selected pages of a PDF as plain text."""
import sys

from pypdf import PdfReader

pdf, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
r = PdfReader(pdf)
for n in range(first - 1, min(last, len(r.pages))):
    print("========== page %d ==========" % (n + 1))
    print(r.pages[n].extract_text())
