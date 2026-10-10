#!/usr/bin/env python3
"""Make the boundary-file output contain ONLY the house surfaces.

FDS writes boundary data for every surface by default, which is why colouring
by wall temperature turned the whole scene blue.  The User Guide gives the
control:

    BNDF_DEFAULT=F on the &MISC line  -> switch boundary output off everywhere
    BNDF_OBST=T on an &OBST line      -> switch it back on for that obstruction

So with BNDF_DEFAULT=F and BNDF_OBST=T only on the house walls and the roof,
the .bf file holds the building envelope alone.  Rendering it then colour-codes
the house and leaves everything else -- ground, trees, hedge, embers -- drawn
normally.
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
SRC = os.path.join(CASE, "garden_tall.fds")
DST = os.path.join(CASE, "house_risk.fds")

s = open(SRC).read()

# 1. switch boundary output off globally
s = s.replace("&MISC ", "&MISC BNDF_DEFAULT=.FALSE., ", 1)

# 2. re-enable it on the house walls and the roof only
s = re.sub(r"(&OBST XB=21\.0,33\.0[^/]*?)\s*/",
           r"\1, BNDF_OBST=.TRUE. /", s)
s = re.sub(r"(&OBST XB=20\.6,33\.4[^/]*?)\s*/",
           r"\1, BNDF_OBST=.TRUE. /", s)

open(DST, "w").write(s.replace("CHID='garden_tall'", "CHID='house_risk'"))

print("MISC line:", [l for l in s.split("\n") if l.startswith("&MISC")])
for l in s.split("\n"):
    if "BNDF_OBST" in l:
        print("enabled:", l.strip()[:80])
