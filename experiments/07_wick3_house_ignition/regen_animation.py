#!/usr/bin/env python3
"""Verify the terrain fix, then regenerate the three-layer animation.

Pass 1: flame volume + embers      -> fireembers/
Pass 2: soot volume                -> smoke/
blend:  0.70*pass1 + 0.30*pass2    -> composited/   ("light smoke")

Also renders one geometry-only frame first and reports whether the olive
skirt is gone (it should match the GRASS surface colour instead).
"""
import os
import shutil
import subprocess
from collections import Counter

from PIL import Image

CASE = os.path.expanduser("~/FDS/cases/garden_loft")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
PY = os.path.expanduser("~/FDS/.venv/bin/python")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")

TIMES = [8, 16, 24, 32, 40, 50, 62, 76, 92, 110]

# true colours, for the verification check
EXPECT = {"GRASS": (138, 129, 62), "LAWN": (96, 160, 64),
          "TRUNK": (105, 78, 52), "CANOPY": (40, 90, 35)}


def ssf(path, subdir, files, prefix, times, viewpoint=True):
    with open(path, "w") as fh:
        fh.write(f"RENDERDIR\n {subdir}\nUNLOADALL\n")
        if viewpoint:
            fh.write("LOADINIFILE\n garden_loft.ini\n")
        for f in files:
            fh.write(f"LOADFILE\n {f}\n")
        if viewpoint:
            fh.write("SETVIEWPOINT\n iso_b\n")
        for t in times:
            fh.write(f"SETTIMEVAL\n {t}.0\nRENDERONCE\n {prefix}_{t:03d}\n")


def render(path, subdir):
    out = os.path.join(CASE, subdir)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(CASE, "garden_loft.ssf"), "w") as fh:
        fh.write(open(path).read())
    subprocess.run([SMV, "-runscript", "garden_loft"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=1200)
    n = len(os.listdir(out))
    print(f"  {subdir}: {n} frames")
    return out


# ---- 1. verification frame ------------------------------------------------
print("verification render (geometry only):")
tmp = os.path.join(CASE, "verify.ssf")
ssf(tmp, "verify", [], "v", [50])
render(tmp, "verify")
png = os.path.join(CASE, "verify", "v_050.png")
if os.path.exists(png):
    im = Image.open(png).convert("RGB")
    c = Counter(im.crop((150, 280, 480, 400)).getdata()).most_common(4)
    print("  colours at the obstruction bases:")
    for col, n in c:
        best = min(EXPECT.items(),
                   key=lambda kv: sum((a - b) ** 2 for a, b in zip(col, kv[1])))
        print(f"    RGB{str(col):18s} {n:6d} px  nearest {best[0]}")

# ---- 2. the two animation passes -----------------------------------------
print("\nrendering passes:")
p1 = os.path.join(CASE, "p1.ssf")
ssf(p1, "fireembers", ["garden_loft_1_3.s3d", "garden_loft_1.prt5"], "f", TIMES)
render(p1, "fireembers")

p2 = os.path.join(CASE, "p2.ssf")
ssf(p2, "smoke", ["garden_loft_1_1.s3d"], "s", TIMES)
render(p2, "smoke")

# ---- 3. blend + gifs ------------------------------------------------------
print("\nblending and building gifs:")
subprocess.run([VENV, os.path.expanduser("~/FDS/composite_smoke.py"),
                os.path.join(CASE, "fireembers"), os.path.join(CASE, "smoke"),
                os.path.join(CASE, "composited"), "0.70"], check=False)
for srcdir, gif in (("composited", "fire_embers_smoke.gif"),
                    ("fireembers", "fire_embers_3d.gif")):
    subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"),
                    os.path.join(CASE, srcdir), os.path.join(CASE, gif), "1.0"],
                   check=False)
    p = os.path.join(CASE, gif)
    print(f"  {gif}: {os.path.getsize(p)} bytes" if os.path.exists(p)
          else f"  {gif}: FAILED")

subprocess.run(["open", os.path.join(CASE, "fire_embers_smoke.gif")], check=False)
print("opened fire_embers_smoke.gif")
