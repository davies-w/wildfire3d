"""Diagnose the spurious salmon quad in the blended ignition frame.

Reports the A and B pixel values in the lower-left region where the wash fires
outside the render box, so the cause can be identified rather than guessed.
"""
import os

import numpy as np
from PIL import Image

CASE = os.path.expanduser("~/FDS/cases/wick3")
A = np.asarray(Image.open(os.path.join(CASE, "norm", "n_280.png")).convert("RGB"), dtype=float)
B = np.asarray(Image.open(os.path.join(CASE, "burn", "b_280.png")).convert("RGB"), dtype=float)

warm = np.clip((B[:, :, 0] - B[:, :, 2] - 20.0) / 120.0, 0, 1)
moved = (np.abs(B - A).max(axis=2) > 25).astype(float)
m = warm * moved

ys, xs = np.where(m > 0.2)
print("washed pixels: %d" % len(xs))
print("x range %d..%d   y range %d..%d" % (xs.min(), xs.max(), ys.min(), ys.max()))
print("right-most washed column:", xs.max(), "(image width %d)" % A.shape[1])

sub = (slice(300, 372), slice(80, 195))
print("lower-left block y300:372 x80:195")
print("  mean A", A[sub].reshape(-1, 3).mean(axis=0).round(1))
print("  mean B", B[sub].reshape(-1, 3).mean(axis=0).round(1))
print("  washed px there:", int((m[sub] > 0.2).sum()))
yy, xx = np.where(m[sub] > 0.2)
if len(xx):
    i, j = yy[0] + 300, xx[0] + 80
    print("  example at (x=%d,y=%d): A=%s B=%s warm=%.2f moved=%.0f"
          % (j, i, A[i, j].astype(int), B[i, j].astype(int), warm[i, j], moved[i, j]))
