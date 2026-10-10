"""When did the tree catch fire?

Counts warm (orange/red) pixels in the tree region of each rendered frame.
On Smokeview's blue->red ramp, R >> B means a hot surface.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import glob
import os

import numpy as np
from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/wick3")
TREE = (170, 200, 340, 360)      # left, top, right, bottom in the frame

print(f"{'t s':>6} {'warm px':>9}")
for f in sorted(glob.glob(os.path.join(CASE, "composited", "c_*.png"))):
    t = int(os.path.basename(f)[2:5])
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    reg = a[TREE[1]:TREE[3], TREE[0]:TREE[2]]
    warm = (reg[:, :, 0] - reg[:, :, 2] > 40) & (reg[:, :, 0] > 140)
    print(f"{t:6d} {int(warm.sum()):9d}")
