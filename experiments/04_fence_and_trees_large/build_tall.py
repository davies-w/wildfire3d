#!/usr/bin/env python3
"""Double the vertical extent of the garden case: 40 x 40 x 12 -> 40 x 40 x 24.

Same 1 m cells, so the cell count doubles (19,200 -> 38,400) and the solve takes
roughly twice as long.  Everything else is unchanged: same house, hedge, trees,
level-set grass, mown lawn, hot lofted embers.

Also writes a matching viewpoint .ini -- the scene bounding box on the last
line has to grow with the domain or Smokeview will frame it wrongly.
"""
import os
import re

CASE = os.path.expanduser("~/FDS/cases/garden_loft")
SRC = os.path.join(CASE, "garden_loft.fds")
DST = os.path.expanduser("~/FDS/cases/garden_tall")

os.makedirs(DST, exist_ok=True)
s = open(SRC).read()

# --- new CHID and a taller mesh
s = s.replace("CHID='garden_loft'", "CHID='garden_tall'")
s = re.sub(r"&MESH[^/]*/",
           "&MESH ID='garden', IJK=40,40,24, XB=0,40, 0,40, 0,24 /",
           s, count=1)

open(os.path.join(DST, "garden_tall.fds"), "w").write(s)
m = re.search(r"&MESH[^/]*/", s)
print("new mesh line:", m.group(0) if m else "NOT FOUND")

# --- viewpoint .ini with a 24 m tall bounding box
ini_src = os.path.join(CASE, "garden_loft.ini")
ini = open(ini_src).read()
# last data line before each viewpoint name holds the scene bbox
ini = re.sub(r"(-\d+\.\d+)\s+(-\d+\.\d+)\s+-0\.012000\s+"
             r"(\d+\.\d+)\s+(\d+\.\d+)\s+12\.012000",
             r"\1 \2 -0.024000 \3 \4 24.024000", ini)
open(os.path.join(DST, "garden_tall.ini"), "w").write(ini)
print("ini bbox lines now:")
for line in ini.split("\n"):
    if "24.024000" in line:
        print("   ", line.strip())
