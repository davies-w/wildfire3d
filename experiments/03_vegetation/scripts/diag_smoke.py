#!/usr/bin/env python3
"""Capture Smokeview's output for the soot pass, with the script correctly
named after the casename."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import shutil
import subprocess

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")

with open(os.path.join(CASE, "garden_tall.ssf"), "w") as fh:
    fh.write("RENDERDIR\n diagout\nUNLOADALL\nLOADINIFILE\n garden_tall.ini\n"
             "LOADFILE\n garden_tall_1_1.s3d\nSETVIEWPOINT\n iso_b\n"
             "SETTIMEVAL\n 50.0\nRENDERONCE\n diag_050\n")

out = os.path.join(CASE, "diagout")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out, exist_ok=True)

r = subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                   capture_output=True, text=True,
                   stdin=subprocess.DEVNULL, timeout=1500)
print("exit code:", r.returncode)
print("frames:", len(os.listdir(out)))
lines = [l for l in (r.stdout + r.stderr).split("\n") if l.strip()]
print("output (last 30 lines):")
for line in lines[-30:]:
    print("   ", line)
