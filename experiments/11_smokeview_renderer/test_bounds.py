#!/usr/bin/env python3
"""Try syntax variants for SETBOUNDBOUNDS.

Documented usage:
    SETBOUNDBOUNDS ivalmin valmin ivalmax valmax quantity_label

It did nothing when the four numbers were on the line after the command and
the label followed them.  Try the command with all args on one line, and the
label on its own line.
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

HEAD = ("RENDERDIR\n risk\nUNLOADALL\nLOADINIFILE\n garden_tall.ini\n"
        "LOADFILE\n garden_tall_1_1.s3d\nSMOKEPROP\n 0.00001\n")
TAIL = ("LOADFILE\n garden_tall_1_1.bf\nSETVIEWPOINT\n iso_b\n"
        "SETTIMEVAL\n 60.0\nRENDERONCE\n {tag}\n")

VARIANTS = {
    "v_oneline": "SETBOUNDBOUNDS 1 20.0 1 350.0 WALL TEMPERATURE\n",
    "v_labelline": "SETBOUNDBOUNDS\n 1 20.0 1 350.0\n WALL TEMPERATURE\n",
}

os.makedirs(os.path.join(CASE, "risk"), exist_ok=True)
for tag, bounds in VARIANTS.items():
    open(SSF, "w").write(HEAD + bounds + TAIL.format(tag=tag))
    r = subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                       capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=900)
    png = os.path.join(CASE, "risk", f"{tag}.png")
    print(f"{tag}: exit={r.returncode} rendered={os.path.exists(png)}")
    for line in (r.stdout + r.stderr).split("\n"):
        if "rror" in line or "hilight" in line.lower():
            print("   ", line.strip())
