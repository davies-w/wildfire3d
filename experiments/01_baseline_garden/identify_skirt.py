#!/usr/bin/env python3
"""Identify the olive 'skirt' at the base of every obstruction.

Recolours EVERY surface in the .smv to a unique, unmistakable colour, renders
one frame, then reports which table entry the skirt's pixels match.

Everything long lives here so the shell command stays one word.
"""
import os
import shutil
import subprocess
import sys

from PIL import Image
from collections import Counter

CASE = os.path.expanduser("~/FDS/cases/garden_loft")
SMV = os.path.join(CASE, "garden_loft.smv")
ORIG = SMV + ".orig"
SMV_BIN = os.path.expanduser(
    "~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")

# every surface -> a unique colour
TABLE = {
    "INERT": (255, 0, 0),
    "GRASS": (0, 255, 0),
    "LAWN": (0, 0, 255),
    "WOOD WALL": (255, 255, 0),
    "ROOF": (255, 0, 255),
    "GLASS": (0, 255, 255),
    "HEDGE": (255, 128, 0),
    "TRUNK": (128, 0, 255),
    "CANOPY": (0, 128, 0),
    "firebrand": (255, 255, 255),
    "SPOT IGN": (0, 0, 0),
}


def patch_all():
    shutil.copy(ORIG, SMV)
    lines = open(SMV).read().split("\n")
    out, cur, hits = [], None, 0
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() == "SURFACE":
            cur = lines[i + 1].strip() if i + 1 < len(lines) else None
            continue
        if cur in TABLE and len(line.split()) >= 6 and line.split()[0].isdigit():
            r, g, b = (v / 255.0 for v in TABLE[cur])
            parts = line.split()
            parts[3], parts[4], parts[5] = f"{r:.5f}", f"{g:.5f}", f"{b:.5f}"
            out[-1] = "  " + "      ".join(parts)
            hits += 1
            cur = None
    open(SMV, "w").write("\n".join(out))
    print(f"patched {hits} surfaces")
    for k, v in TABLE.items():
        print(f"   {k:12s} -> RGB{v}")


def render():
    ssf = os.path.join(CASE, "garden_loft.ssf")
    with open(ssf, "w") as fh:
        fh.write("RENDERDIR\n keyall\nUNLOADALL\nLOADINIFILE\n garden_loft.ini\n"
                 "SETVIEWPOINT\n iso_b\nSETTIMEVAL\n 50.0\nRENDERONCE\n all_050\n")
    out = os.path.join(CASE, "keyall")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    subprocess.run([SMV_BIN, "-runscript", "garden_loft"],
                   cwd=CASE, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                   timeout=600)
    png = os.path.join(out, "all_050.png")
    print("rendered:", png, os.path.exists(png))
    return png


def analyse(png):
    im = Image.open(png).convert("RGB")
    # sample the skirt under the trees
    skirt = Counter(im.crop((150, 280, 480, 400)).getdata()).most_common(6)
    print("\ndominant colours at the obstruction bases:")
    for col, n in skirt:
        match = [k for k, v in TABLE.items()
                 if all(abs(a - b) < 6 for a, b in zip(col, v))]
        print(f"   RGB{str(col):18s} {n:6d} px   matches {match or 'NO TABLE ENTRY'}")


if __name__ == "__main__":
    patch_all()
    analyse(render())
