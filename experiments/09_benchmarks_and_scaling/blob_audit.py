"""Audit FDS output volume by file type, and test compressibility.

Decides the storage question with measurements rather than intuition: which
suffixes dominate, whether the data is large because of many cases or one big
run, and what fraction a gzip saves.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, collections

ROOT = FDS_ROOT
by_ext = collections.Counter()
n_ext = collections.Counter()
cases = collections.Counter()

for base in ("cases", "runs"):
    for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            ext = os.path.splitext(f)[1].lower() or "(none)"
            by_ext[ext] += sz
            n_ext[ext] += 1
            rel = os.path.relpath(p, os.path.join(ROOT, base)).split(os.sep)[0]
            cases[rel] += sz

print("=== bytes by extension ===")
for e, s in by_ext.most_common(14):
    print("  %-8s %8.1f MB  %6d files" % (e, s / 1e6, n_ext[e]))
print("  TOTAL    %8.1f MB" % (sum(by_ext.values()) / 1e6))
print()
print("=== top cases ===")
for c, s in cases.most_common(8):
    print("  %-20s %8.1f MB" % (c, s / 1e6))
