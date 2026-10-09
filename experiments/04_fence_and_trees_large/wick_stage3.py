"""Stage 3: boundary-file filtering for the house-only colour bar.

BNDF_DEFAULT=F on MISC turns boundary output off everywhere; BNDF_OBST=T on an
OBST turns it back on for the house walls and roof only.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import re

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
p = os.path.join(CASE, "wick.fds")
s = open(p).read()

s = s.replace("&MISC ", "&MISC BNDF_DEFAULT=.FALSE., ", 1)
for tag in ("XB=32.0,44.0, 26.0,34.0", "XB=31.6,44.4, 25.6,34.4"):
    s = re.sub(r"(&OBST " + re.escape(tag) + r"[^/]*?)\s*/",
               r"\1, BNDF_OBST=.TRUE. /", s)

open(p, "w").write(s)
print([l.strip()[:70] for l in s.split("\n") if l.startswith("&MISC")])
for l in s.split("\n"):
    if "BNDF_OBST" in l:
        print("enabled:", l.strip()[:70])
