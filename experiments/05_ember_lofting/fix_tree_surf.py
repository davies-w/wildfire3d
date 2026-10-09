"""Restore SURF_ID on the tree obstructions.

My stage-2 script rewrote the tree OBST lines with a regex whose pattern
included SURF_ID='TRUNK' / SURF_ID='CANOPY', and the replacement text omitted
it.  So all ten tree obstructions ended up as bare &OBST lines with no surface
at all, defaulting to the domain's default surface.

Fix: any bare &OBST line whose z-range looks like a trunk gets TRUNK, and one
whose z-range looks like a canopy gets CANOPY.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import re

p = os.path.join(FDS_ROOT, "cases/garden_tall/wick.fds")
s = open(p).read()

trunk_z = (" 0.0,3.5 /", " 0.0,2.5 /", " 0.0,4.0 /")
canopy_z = (" 3.5,8.0 /", " 2.5,5.5 /", " 3.5,7.5 /")

n = 0
for line in s.split("\n"):
    if not line.startswith("&OBST XB=") or "SURF_ID" in line:
        continue
    for z in trunk_z:
        if line.endswith(z):
            s = s.replace(line, line[:-2] + ", SURF_ID='TRUNK' /", 1)
            n += 1
            break
    else:
        for z in canopy_z:
            if line.endswith(z):
                s = s.replace(line, line[:-2] + ", SURF_ID='CANOPY' /", 1)
                n += 1
                break

open(p, "w").write(s)
print("lines fixed:", n)
print("trunk obstructions:", s.count("SURF_ID='TRUNK'"))
print("canopy obstructions:", s.count("SURF_ID='CANOPY'"))
print("bare OBST lines left:",
      len([l for l in s.split("\n")
           if l.startswith("&OBST XB=") and "SURF_ID" not in l]))
