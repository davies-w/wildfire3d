#!/usr/bin/env python3
"""Measure the RAW (unblended) render, not the composited one.

The composite multiplies the base by 0.70 wherever smoke sits, which darkens
everything and can fake a "GRASS x0.7" match.  The raw frame is the honest
measurement.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
from collections import Counter

from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
TABLE = {"GRASS": (138, 129, 62), "LAWN": (96, 160, 64), "TRUNK": (105, 78, 52),
         "CANOPY": (40, 90, 35), "HEDGE": (52, 98, 38), "ROOF": (169, 169, 169)}


def nearest(col):
    best, dist = None, 1e9
    for k, v in TABLE.items():
        for scale in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            cand = tuple(c * scale for c in v)
            d = sum((a - b) ** 2 for a, b in zip(col, cand))
            if d < dist:
                dist, best = d, (k, scale)
    return best, dist ** 0.5


for png in ("fireembers/ft_050.png", "composited/c_050.png"):
    p = os.path.join(CASE, png)
    if not os.path.exists(p):
        print(png, "missing")
        continue
    im = Image.open(p).convert("RGB")
    print(f"\n{png}")
    for col, n in Counter(im.crop((150, 280, 480, 400)).getdata()).most_common(5):
        (name, scale), d = nearest(col)
        print(f"   RGB{str(col):18s} {n:6d} px  nearest {name} x{scale:.1f} (d={d:.0f})")
