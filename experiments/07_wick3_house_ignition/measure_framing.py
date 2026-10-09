"""Measure how much geometry touches each image edge, to test framing.

The render truncated the foreground. Rather than guess at the undocumented
VIEWPOINT5 fields, vary the documented ZOOM keyword and measure whether
geometry still runs off an edge.

Smokeview's info bar occupies the bottom rows, so those are excluded -- a
scene that legitimately fills the frame would touch it.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import numpy as np
from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/wick3")
INFO_BAR = 34


def report(tag, png):
    a = np.asarray(Image.open(png).convert("RGB"), int)
    body = a.min(axis=2) <= 235
    body = body[: a.shape[0] - INFO_BAR, :]
    h, w = body.shape
    ys, xs = np.nonzero(body)
    if not len(ys):
        print("%-16s no geometry" % tag)
        return
    print("%-16s rows %3d-%3d of %3d  cols %3d-%3d of %3d   contact "
          "top=%d bottom=%d left=%d right=%d"
          % (tag, ys.min(), ys.max(), h, xs.min(), xs.max(), w,
             body[:2, :].sum(), body[h - 2:, :].sum(),
             body[:, :2].sum(), body[:, w - 2:].sum()))


d = os.path.join(CASE, "zoom")
if not os.path.isdir(d):
    print("no %s yet" % d)
    sys.exit(0)
for name in sorted(os.listdir(d)):
    if name.endswith(".png"):
        report(name[:-4], os.path.join(d, name))
