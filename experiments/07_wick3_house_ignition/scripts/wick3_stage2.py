"""Stage 2 for wick3: fence, ladder tree and trees repositioned to the
smaller 32 x 24 m domain."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os

P = os.path.join(FDS_ROOT, "cases/wick3/wick3.fds")
s = open(P).read()

MAP = [
    # fence: west, south, north, spur
    ("XB=15.0,15.5, 12.0,28.0, 0.0,1.8", "XB=10.5,11.0, 4.0,20.0, 0.0,1.8"),
    ("XB=15.5,36.0, 11.5,12.0, 0.0,1.8", "XB=11.0,31.0, 3.5,4.0, 0.0,1.8"),
    ("XB=15.5,36.0, 28.0,28.5, 0.0,1.8", "XB=11.0,31.0, 20.0,20.5, 0.0,1.8"),
    ("XB=15.5,24.0, 19.5,20.0, 0.0,1.8", "XB=11.0,18.0, 11.5,12.0, 0.0,1.8"),
    # ladder tree: canopy over the spur, 1 cell from the house wall at x=18
    ("XB=22.0,23.0, 21.0,22.0, 0.0,1.8", "XB=16.0,17.0, 12.5,13.5, 0.0,1.8"),
    ("XB=20.5,23.5, 18.5,24.5, 1.8,6.5", "XB=14.5,17.5, 10.0,16.0, 1.8,6.5"),
    # trees out in the grass
    ("XB=5.0,6.0, 20.0,21.0, 0.0,2.0", "XB=4.0,5.0, 11.0,12.0, 0.0,2.0"),
    ("XB=3.5,7.5, 18.0,23.0, 2.0,6.5", "XB=2.5,6.5, 9.0,14.0, 2.0,6.5"),
    ("XB=10.0,11.0, 32.0,33.0, 0.0,2.0", "XB=7.0,8.0, 18.0,19.0, 0.0,2.0"),
    ("XB=8.5,12.5, 30.0,35.0, 2.0,6.5", "XB=5.5,9.5, 16.0,21.0, 2.0,6.5"),
    ("XB=8.0,9.0, 8.0,9.0, 0.0,1.5", "XB=4.0,5.0, 20.0,21.0, 0.0,1.5"),
    ("XB=6.5,10.5, 6.0,11.0, 1.5,5.0", "XB=2.5,6.5, 18.0,23.0, 1.5,5.0"),
    ("XB=12.0,13.0, 25.0,26.0, 0.0,1.5", "XB=8.0,9.0, 4.0,5.0, 0.0,1.5"),
    ("XB=10.5,14.5, 23.0,28.0, 1.5,5.0", "XB=6.5,10.5, 2.0,7.0, 1.5,5.0"),
]

for old, new in MAP:
    assert old in s, f"not found: {old}"
    s = s.replace(old, new)

open(P, "w").write(s)

# sanity: nothing outside the 0-32 / 0-24 domain
import re
bad = [l for l in s.split("\n")
       if l.startswith("&OBST")
       and (max(float(v) for v in re.findall(r"XB=([\d.,\s-]+)/", l)[0].split(","))) > 32.0]
print("obstructions past x=32:", len(bad))
print("mesh:", re.search(r"&MESH[^/]*/", s).group(0))
print("lines:", len(s.split("\n")))
