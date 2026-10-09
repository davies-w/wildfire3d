"""One test frame of the fence + house temperature view."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import subprocess

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
OUT = os.path.join(CASE, "wicktemp")
os.makedirs(OUT, exist_ok=True)

open(os.path.join(CASE, "wick.ssf"), "w").write(
    "RENDERDIR\n wicktemp\nUNLOADALL\nLOADINIFILE\n wick.ini\n"
    "LOADFILE\n wick_1_3.s3d\nLOADFILE\n wick_1.prt5\n"
    "LOADFILE\n wick_1_1.bf\nSETVIEWPOINT\n iso_b\n"
    "SETTIMEVAL\n 90.0\nRENDERONCE\n wt_090\n")

r = subprocess.run([SMV, "-runscript", "wick"], cwd=CASE,
                   capture_output=True, text=True,
                   stdin=subprocess.DEVNULL, timeout=900)
print("exit", r.returncode, sorted(os.listdir(OUT)))
