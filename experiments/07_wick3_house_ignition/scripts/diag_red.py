"""Where did pass B put the burning-rate maximum?

Pass B shows blue where pass A shows the canopy, and blue is the bottom of the
ramp.  Either Smokeview never drew the canopy's burning rate, or the two passes
placed the scene differently so the red lands somewhere else on screen.

Looking at the ramp in the render, the top of the scale is a strong red/orange.
This finds those pixels and reports their bounding box, and separately reports
what fraction of the image is on the ramp at all.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os

import numpy as np
from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/wick3")
T = 350
A = np.asarray(Image.open(os.path.join(CASE, "norm", "n_%03d.png" % T)).convert("RGB"), dtype=float)
B = np.asarray(Image.open(os.path.join(CASE, "burn", "b_%03d.png" % T)).convert("RGB"), dtype=float)

# ramp colourbar occupies the right edge; measure the actual ramp pixels from it
bar = B[:, 480:640]
print("colour bar sample colours (top to bottom):")
for frac in (0.05, 0.2, 0.4, 0.6, 0.8, 0.95):
    row = int(frac * bar.shape[0])
    print("  %4.0f%% down: %s" % (frac * 100, bar[row, 20].astype(int)))

hot = (B[:, :, 0] > 180) & (B[:, :, 1] < 130) & (B[:, :, 2] < 90)
print("\nstrong red/orange (top of ramp) in pass B: %d pixels" % int(hot.sum()))
if hot.sum():
    ys, xs = np.where(hot)
    print("  bbox  x %d..%d  y %d..%d" % (xs.min(), xs.max(), ys.min(), ys.max()))
    # only the scene, not the colourbar
    scene = xs < 470
    if scene.any():
        print("  in scene: %d pixels, bbox x %d..%d y %d..%d"
              % (int(scene.sum()), xs[scene].min(), xs[scene].max(),
                 ys[scene].min(), ys[scene].max()))

blue = (B[:, :, 2] > 140) & (B[:, :, 2] - B[:, :, 0] > 40)
print("\nblue (ramp bottom = zero burning) in scene: %d pixels" % int((blue & (np.arange(B.shape[1])[None, :] < 470)).sum()))
print("canopy screen bbox from pass A was x 172..418  y 228..389")
