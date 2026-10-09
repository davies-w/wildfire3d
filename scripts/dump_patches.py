"""Dump every patch bbox in the wick3c boundary data, to fix the box mapping.

ign_state.py (now surface_temp.py) found nothing for ROOF or FENCE. Rather than
guess at coordinates, list what patches actually exist and where.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from surface_temp import CASE, CHID, PATCH, bbox, dump  # noqa: E402

seen = {}
for orient in (1, -1, 2, -2, 3, -3):
    p = dump(orient, 0)
    if not p:
        print("orientation %-3d no output" % orient)
        continue
    n = 0
    for line in open(p):
        if not line.startswith("Patch"):
            continue
        m = PATCH.match(line.rstrip())
        if not m:
            continue
        box = bbox(m.group(2) + "," + m.group(3) + "," + m.group(4))
        if any(b is None for b in box):
            continue
        key = (orient, tuple(round(v, 2) for b in box for v in b))
        seen[key] = seen.get(key, 0) + 1
        n += 1
    print("orientation %-3d %d patches" % (orient, n))

print("\nall distinct patch bboxes (orientation, x0,x1, y0,y1, z0,z1):")
for (orient, coords), _ in sorted(seen.items()):
    print("  o%-3d x %6.2f-%-6.2f y %6.2f-%-6.2f z %6.2f-%-6.2f"
          % (orient, coords[0], coords[1], coords[2], coords[3], coords[4], coords[5]))
