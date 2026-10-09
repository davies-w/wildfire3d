"""Does the house wall actually ignite in the animation?

The measured data says the x=18 wall face passes 350 C between t=200 and 248,
and is fully involved by t=300. So in the blend, the wall region should go
orange. Track it frame by frame.
"""
import sys, os

ROOT = "/Users/wdavies/pi/wildfire3d"
sys.path.insert(0, ROOT)
from paths import FDS_ROOT  # noqa: E402

import numpy as np
from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/wick3")
TIMES = [40, 90, 140, 180, 200, 220, 240, 260, 280, 300, 320, 350]
HOT = np.array([235, 70, 20])
WALL = np.array([178, 147, 108])   # WOOD WALL at 0.8 shading

print("%-5s %-14s %-14s %s" % ("t", "wall px (norm)", "wall px (blend)", "hot px in wall box"))
for t in TIMES:
    a = np.asarray(Image.open(os.path.join(CASE, "norm/n_%03d.png" % t)).convert("RGB"), int)
    i = np.asarray(Image.open(os.path.join(CASE, "ignition_clean/i_%03d.png" % t)).convert("RGB"), int)
    wallA = np.all(np.abs(a - WALL) <= 3, axis=2)
    wallI = np.all(np.abs(i - WALL) <= 3, axis=2)
    if wallA.sum() < 50:
        print("%-5d  wall region not found" % t)
        continue
    ys, xs = np.nonzero(wallA)          # the box, from the earliest frame
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    hot = np.all(np.abs(i[y0:y1 + 1, x0:x1 + 1] - HOT) <= 12, axis=2)
    print("%-5d %-14d %-14d %d" % (t, wallA.sum(), wallI.sum(), hot.sum()))
