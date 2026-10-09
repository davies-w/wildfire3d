"""Check whether the fence burned, from the flame volume.

The flame volume covers the whole domain regardless of the boundary-file
settings, so a burning fence must show up in it.  Rendering from above makes
the fence line and its spur obvious: they should appear as a lit path if flame
travelled along them.

One frame per invocation, as multi-frame runs of the large volumes crash.
"""
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
OUT = os.path.join(CASE, "flamecheck")
os.makedirs(OUT, exist_ok=True)

for t in (60, 90, 120, 150):
    open(os.path.join(CASE, "wick.ssf"), "w").write(
        f"RENDERDIR\n flamecheck\nUNLOADALL\nLOADINIFILE\n wick.ini\n"
        f"LOADFILE\n wick_1_3.s3d\nSETVIEWPOINT\n iso_b\n"
        f"SETTIMEVAL\n {t}.0\nRENDERONCE\n fl_{t:03d}\n")
    subprocess.run([SMV, "-runscript", "wick"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=900)

print("frames:", sorted(os.listdir(OUT)))
