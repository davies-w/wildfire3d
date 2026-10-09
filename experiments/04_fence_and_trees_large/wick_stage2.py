"""Stage 2: swap the hedge for a wooden fence that rings the lawn and runs a
spur to the house -- the 'wick'.

Fence run: west, south, north and east sides of the lawn, plus a spur from the
west fence to the house's west wall.  The spur is the continuous fuel path --
flame should travel along it and arrive at the building.
"""
import os
import re

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
s = open(os.path.join(CASE, "wick.fds")).read()

FENCE = [
    (19.0, 20.0, 18.0, 42.0),   # west side of the lawn
    (20.0, 54.0, 18.0, 19.0),   # south
    (20.0, 54.0, 41.0, 42.0),   # north
    (53.0, 54.0, 19.0, 41.0),   # east
    (20.0, 32.0, 29.0, 30.0),   # SPUR to the house west wall
]
block = "".join(
    f"&OBST XB={a},{b}, {c},{d}, 0.0,1.8, SURF_ID='FENCE' /\n"
    for a, b, c, d in FENCE
).rstrip()
s = re.sub(r"&OBST XB=15\.0,16\.0[^/]*/", block, s, count=1)

# trees, moved into the grass west of the fence (x < 20)
trunks = [(5.5, 6.5, 21.5, 22.5, 0.0, 3.5), (11.5, 12.5, 39.5, 40.5, 0.0, 3.5),
          (9.5, 10.5, 11.5, 12.5, 0.0, 2.5), (13.5, 14.5, 49.5, 50.5, 0.0, 2.5),
          (15.5, 16.5, 29.5, 30.5, 0.0, 3.5)]
canopies = [(4.0, 8.0, 20.0, 24.0, 3.5, 8.0), (10.0, 14.0, 38.0, 42.0, 3.5, 8.0),
            (8.5, 11.5, 10.5, 13.5, 2.5, 5.5), (12.5, 15.5, 48.5, 51.5, 2.5, 5.5),
            (14.0, 18.0, 28.0, 32.0, 3.5, 8.0)]

for pat, rows in ((r"&OBST XB=[^/]*SURF_ID='TRUNK' /", trunks),
                  (r"&OBST XB=[^/]*SURF_ID='CANOPY' /", canopies)):
    it = iter(rows)

    def sub(_m, it=it):
        a, b, c, d, e, f = next(it)
        extra = ", BNDF_OBST=.TRUE." if False else ""
        return f"&OBST XB={a},{b}, {c},{d}, {e},{f}{extra} /"

    s, n = re.subn(pat, sub, s)
    print("replaced", n, "obstructions")

open(os.path.join(CASE, "wick.fds"), "w").write(s)
print("fence pieces:", s.count("SURF_ID='FENCE'"))
print("hedge left:", "SURF_ID='HEDGE'" in s)
