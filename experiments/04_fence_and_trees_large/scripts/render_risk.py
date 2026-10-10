#!/usr/bin/env python3
"""Render the 'too hot' overlay for the building surfaces.

SETBOUNDBOUNDS sets the colorbar range for a boundary file and must come
BEFORE it is loaded; HILIGHTMAXVALS paints anything above that maximum in a
solid colour.  So max = ignition temperature + red hilight = the building
lights up exactly where it is too hot.

A 3-D volume file is loaded first because SETTIMEVAL needs a global time
array, which boundary files alone do not define.
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
SSF = os.path.join(CASE, "garden_tall.ssf")

script = """RENDERDIR
 risk
UNLOADALL
LOADINIFILE
 garden_tall.ini
LOADFILE
 garden_tall_1_1.s3d
SETBOUNDBOUNDS
 1 20.0 1 {thr} WALL TEMPERATURE
HILIGHTMAXVALS
 1 1.0 0.0 0.0
LOADFILE
 garden_tall_1_1.bf
SETVIEWPOINT
 iso_b
SETTIMEVAL
 60.0
RENDERONCE
 risk_{tag}
"""

os.makedirs(os.path.join(CASE, "risk"), exist_ok=True)
for tag, thr in (("180", 180.0), ("350", 350.0)):
    open(SSF, "w").write(script.format(thr=thr, tag=tag))
    r = subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                       capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=900)
    png = os.path.join(CASE, "risk", f"risk_{tag}.png")
    print(f"thr={thr}: exit={r.returncode} rendered={os.path.exists(png)}")
    for line in (r.stdout + r.stderr).split("\n"):
        if "rror" in line or "not defined" in line:
            print("   ", line.strip())
