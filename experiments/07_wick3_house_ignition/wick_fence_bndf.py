"""Enable boundary-file output on the fence as well as the house.

BNDF_OBST only controls which surfaces get written to the .bf file, so this
changes no physics -- it just means the fence will have temperature data and
can be colour-coded.

Fence and house on the same colour bar is what makes the wick visible: if heat
tracks along the spur toward the building, the fence temperature should show a
gradient along that path.
"""
import os

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
p = os.path.join(CASE, "wick.fds")
s = open(p).read()

s = s.replace("SURF_ID='FENCE' /", "SURF_ID='FENCE', BNDF_OBST=.TRUE. /")
open(p, "w").write(s)

for l in s.split("\n"):
    if "BNDF_OBST" in l:
        print(l.strip()[:76])
