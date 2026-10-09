#!/usr/bin/env python3
"""Test whether removing the TERRAIN entry from the .smv removes the skirt.

The .smv has a block:

    TERRAIN     1
     garden_loft_1.ter

Dropping those two lines should stop Smokeview drawing the terrain -- without
deleting the file (which broke the render earlier).  If the skirt disappears,
it is confirmed as the terrain, and the real surface colours take over.
"""
import os
import shutil
import subprocess

from PIL import Image
from collections import Counter

CASE = os.path.expanduser("~/FDS/cases/garden_loft")
SMV = os.path.join(CASE, "garden_loft.smv")
SMV_BIN = os.path.expanduser(
    "~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")

lines = open(SMV).read().split("\n")
out, i, removed = [], 0, 0
while i < len(lines):
    if lines[i].startswith("TERRAIN"):
        i += 2                      # skip the TERRAIN line and its filename
        removed += 1
        continue
    out.append(lines[i])
    i += 1
open(SMV, "w").write("\n".join(out))
print(f"removed {removed} TERRAIN block(s) from the .smv")

with open(os.path.join(CASE, "garden_loft.ssf"), "w") as fh:
    fh.write("RENDERDIR\n noter2\nUNLOADALL\nLOADINIFILE\n garden_loft.ini\n"
             "SETVIEWPOINT\n iso_b\nSETTIMEVAL\n 50.0\nRENDERONCE\n nt_050\n")

outdir = os.path.join(CASE, "noter2")
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
subprocess.run([SMV_BIN, "-runscript", "garden_loft"], cwd=CASE,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
               stdin=subprocess.DEVNULL, timeout=600)

png = os.path.join(outdir, "nt_050.png")
print("rendered:", os.path.exists(png))
if os.path.exists(png):
    im = Image.open(png).convert("RGB")
    c = Counter(im.crop((150, 280, 480, 400)).getdata()).most_common(5)
    print("\ndominant colours at the obstruction bases now:")
    for col, n in c:
        print(f"   RGB{str(col):18s} {n:6d} px")
