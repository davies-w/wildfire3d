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

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")

# sample each rendered frame to find the warmest house pixels.  The colour bar
# is a blue->red ramp, so "warm" means red channel well above blue.
for f in sorted(glob.glob(os.path.join(CASE, "hr", "hr_*.png"))):
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    # the colour bar strip is on the right; sample the scene only
    scene = a[:, :, :]
    warm = (scene[:, :, 0] - scene[:, :, 2] > 60) & (scene[:, :, 0] > 150)
    print(f"{os.path.basename(f)}: warm pixels {int(warm.sum()):6d}")
