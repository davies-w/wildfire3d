"""Why did the blend leave the canopy green when the data says it is burning?

Takes the canopy's own geometry colour in pass A (CANOPY RGB 40,90,35), finds
those pixels, and reports what pass B has at the same place and what the blend
computed.  If B is not warm there, the burning-rate pass never drew the canopy
-- so the fault is in the render, not the blend.
"""
import os

import numpy as np
from PIL import Image

CASE = os.path.expanduser("~/FDS/cases/wick3")
T = 350
A = np.asarray(Image.open(os.path.join(CASE, "norm", "n_%03d.png" % T)).convert("RGB"), dtype=float)
B = np.asarray(Image.open(os.path.join(CASE, "burn", "b_%03d.png" % T)).convert("RGB"), dtype=float)

target = np.array([40.0, 90.0, 35.0])
d = np.abs(A - target).max(axis=2)
mask = d < 14
print("pass A pixels matching CANOPY colour %s : %d" % (target.astype(int), int(mask.sum())))

if mask.sum():
    ys, xs = np.where(mask)
    print("  screen bbox  x %d..%d   y %d..%d" % (xs.min(), xs.max(), ys.min(), ys.max()))
    print("  mean A %s" % A[mask].mean(axis=0).round(1))
    print("  mean B %s" % B[mask].mean(axis=0).round(1))

warm = np.clip((B[:, :, 0] - B[:, :, 2] - 20.0) / 120.0, 0, 1)
moved = (np.abs(B - A).max(axis=2) > 25).astype(float)
whiteA = A.min(axis=2) > 235
colB = (B.max(axis=2) - B.min(axis=2)) > 40
cbar = (whiteA & colB).mean(axis=0) > 0.20
m = warm * moved
m[:, cbar] = 0.0
m[whiteA] = 0.0

if mask.sum():
    print("  mean warm on canopy %.3f" % warm[mask].mean())
    print("  mean moved on canopy %.2f" % moved[mask].mean())
    print("  mean wash on canopy  %.3f" % m[mask].mean())

# what IS being washed, and roughly where
w = m > 0.25
print("\nwashed pixels overall: %d" % int(w.sum()))
if w.sum():
    ys, xs = np.where(w)
    print("  washed bbox  x %d..%d  y %d..%d" % (xs.min(), xs.max(), ys.min(), ys.max()))
