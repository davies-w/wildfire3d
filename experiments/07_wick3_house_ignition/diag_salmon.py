"""Is the salmon quad static geometry?  Compare its presence across passes."""
import sys, os

ROOT = "/Users/wdavies/pi/wildfire3d"
sys.path.insert(0, ROOT)
from paths import FDS_ROOT  # noqa: E402

import numpy as np
from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/wick3")
SALMON = np.array([178, 147, 108])

for tag, name in [("A norm", "norm/n_280.png"), ("B burn", "burn/b_280.png"),
                  ("blend", "ignition_clean/i_280.png")]:
    im = np.asarray(Image.open(os.path.join(CASE, name)).convert("RGB"), int)
    hit = np.all(np.abs(im - SALMON) <= 2, axis=2)
    ys, xs = np.nonzero(hit)
    box = "" if not len(ys) else " rows %d-%d cols %d-%d" % (ys.min(), ys.max(), xs.min(), xs.max())
    print("%-7s salmon px = %-6d%s" % (tag, len(ys), box))

smv = open(os.path.join(CASE, "wick3c.smv"), errors="replace").read()
print("\n--- raw SURFACE block ---")
lines = smv.splitlines()
start = next(i for i, l in enumerate(lines) if l.strip() == "SURFACE")
for l in lines[start - 1:start + 22]:
    print(repr(l[:100]))
