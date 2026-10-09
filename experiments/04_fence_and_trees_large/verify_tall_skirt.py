#!/usr/bin/env python3
"""Check whether the olive skirt is really gone in the taller case.

Smokeview draws the .ter terrain with its own colour, outside the SURFACE
table.  If the skirt is still terrain, its pixels will match NO surface colour.
If the strip worked, the skirt area should match the GRASS surface colour
(138,129,62) under lighting.

Also reports whether the .smv still has a TERRAIN block.
"""
import os
from collections import Counter

from PIL import Image

CASE = os.path.expanduser("~/FDS/cases/garden_tall")

# --- is the TERRAIN block still in the .smv?
smv = os.path.join(CASE, "garden_tall.smv")
lines = open(smv).read().split("\n")
print("TERRAIN block present in .smv:",
      any(l.startswith("TERRAIN") for l in lines))

# --- sample the render
png = os.path.join(CASE, "composited", "c_050.png")
im = Image.open(png).convert("RGB")

TABLE = {"GRASS": (138, 129, 62), "LAWN": (96, 160, 64), "TRUNK": (105, 78, 52),
         "CANOPY": (40, 90, 35), "HEDGE": (52, 98, 38)}


def nearest(col):
    best, dist = None, 1e9
    for k, v in TABLE.items():
        # compare hue-ish: scale the surface colour to match brightness
        lum = max(sum(col), 1)
        for scale in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            cand = tuple(c * scale for c in v)
            d = sum((a - b) ** 2 for a, b in zip(col, cand))
            if d < dist:
                dist, best = d, (k, scale)
    return best, dist ** 0.5


print("\ncolours at the obstruction bases:")
for col, n in Counter(im.crop((150, 280, 480, 400)).getdata()).most_common(5):
    (name, scale), d = nearest(col)
    print(f"   RGB{str(col):18s} {n:6d} px   nearest {name} x{scale:.1f} (d={d:.0f})")
