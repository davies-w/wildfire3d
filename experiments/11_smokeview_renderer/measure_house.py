import glob
import os

import numpy as np
from PIL import Image

CASE = os.path.expanduser("~/FDS/cases/garden_tall")

# sample each rendered frame to find the warmest house pixels.  The colour bar
# is a blue->red ramp, so "warm" means red channel well above blue.
for f in sorted(glob.glob(os.path.join(CASE, "hr", "hr_*.png"))):
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    # the colour bar strip is on the right; sample the scene only
    scene = a[:, :, :]
    warm = (scene[:, :, 0] - scene[:, :, 2] > 60) & (scene[:, :, 0] > 150)
    print(f"{os.path.basename(f)}: warm pixels {int(warm.sum()):6d}")
