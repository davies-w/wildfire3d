#!/usr/bin/env python3
"""Restore true surface colours and strip the TERRAIN block from the .smv.

Smokeview draws the .ter terrain with its own colour, outside the SURFACE
table, which is what produced the olive 'skirt' at the base of every
obstruction.  Removing the two-line TERRAIN block makes the ground draw from
the surface table instead, so surface colours behave as specified.

The .ter file itself is left on disk -- deleting it breaks the render.
"""
import os

CASE = os.path.expanduser("~/FDS/cases/garden_loft")
SMV = os.path.join(CASE, "garden_loft.smv")
ORIG = SMV + ".orig"

# start from the untouched colours
open(SMV, "w").write(open(ORIG).read())

lines = open(SMV).read().split("\n")
out, i, removed = [], 0, 0
while i < len(lines):
    if lines[i].startswith("TERRAIN"):
        i += 2
        removed += 1
        continue
    out.append(lines[i])
    i += 1
open(SMV, "w").write("\n".join(out))

print(f"restored true colours from {os.path.basename(ORIG)}")
print(f"removed {removed} TERRAIN block(s)")
print("TERRAIN still present?", any(l.startswith("TERRAIN") for l in out))
