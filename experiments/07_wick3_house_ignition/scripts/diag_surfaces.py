"""Name the surface whose RGB matches the salmon quad.

The .smv SURFACE block is positional: name, then [temperature, rate], then a
line of 7 numbers whose 4th-6th are R,G,B as fractions of 255.
"""
import sys, os

ROOT = "/Users/wdavies/pi/wildfire3d"
sys.path.insert(0, ROOT)
from paths import FDS_ROOT  # noqa: E402

CASE = os.path.join(FDS_ROOT, "cases/wick3")
lines = open(os.path.join(CASE, "wick3c.smv"), errors="replace").read().splitlines()

surfaces, i = [], 0
while i < len(lines) - 3:
    if lines[i].strip() == "SURFACE":
        nums = lines[i + 3].split()
        if len(nums) >= 7:
            r, g, b = (float(x) * 255 for x in nums[3:6])
            surfaces.append((lines[i + 1].strip(), round(r), round(g), round(b)))
    i += 1

TARGET = (178, 147, 108)
best = None
print("%-16s %-16s %s" % ("SURFACE", "RGB in .smv", "distance from salmon"))
for name, r, g, b in surfaces:
    d = abs(r - TARGET[0]) + abs(g - TARGET[1]) + abs(b - TARGET[2])
    mark = ""
    if best is None or d < best[0]:
        best, mark = (d, name, (r, g, b)), "   <-- closest"
    print("%-16s (%3d,%3d,%3d)   %5d%s" % (name, r, g, b, d, mark))

print("\nclosest to %s: %s at %s (distance %d)" % (TARGET, best[1], best[2], best[0]))
