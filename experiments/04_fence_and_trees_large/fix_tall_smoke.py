#!/usr/bin/env python3
"""Render the soot pass one frame per Smokeview invocation.

Multi-frame renders of large volume files crash Smokeview intermittently, and
because the earlier version discarded stdout/stderr the failure was silent.
Single-frame invocations have been reliable throughout, so do it that way.

Then blend with the (already rendered) flame+ember pass and rebuild the gif.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, VENV, VENV_PY  # noqa: E402

import os
import shutil
import subprocess

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = VENV_PY

TIMES = [8, 16, 24, 32, 40, 50, 62, 76, 92, 110]
out = os.path.join(CASE, "smoke")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out, exist_ok=True)

ok = 0
for t in TIMES:
    with open(os.path.join(CASE, "garden_tall.ssf"), "w") as fh:
        fh.write("RENDERDIR\n smoke\nUNLOADALL\nLOADINIFILE\n garden_tall.ini\n"
                 "LOADFILE\n garden_tall_1_1.s3d\nSETVIEWPOINT\n iso_b\n"
                 f"SETTIMEVAL\n {t}.0\nRENDERONCE\n s_{t:03d}\n")
    r = subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                       capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=600)
    got = os.path.exists(os.path.join(out, f"s_{t:03d}.png"))
    ok += got
    if not got:
        err = [l for l in (r.stdout + r.stderr).split("\n") if "rror" in l]
        print(f"  t={t}: FAILED exit={r.returncode} {err[:1]}")
print(f"smoke pass: {ok}/{len(TIMES)} frames")

if ok == len(TIMES):
    subprocess.run([VENV, os.path.join(FDS_ROOT, "composite_smoke.py"),
                    os.path.join(CASE, "fireembers"), out,
                    os.path.join(CASE, "composited"), "0.70"], check=False)
    subprocess.run([VENV, os.path.join(FDS_ROOT, "make_gif.py"),
                    os.path.join(CASE, "composited"),
                    os.path.join(CASE, "tall_fire_smoke.gif"), "1.0"], check=False)
    g = os.path.join(CASE, "tall_fire_smoke.gif")
    if os.path.exists(g):
        print(f"tall_fire_smoke.gif: {os.path.getsize(g)} bytes")
        subprocess.run(["open", g], check=False)
        print("opened")
