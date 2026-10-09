"""Pick a smoke extinction coefficient for wick4 by measuring, not guessing.

SMOKEPROP = 300 was tuned on experiment 07's soot density. wick4 burns less, so
its plume is fainter and at 300 it is nearly invisible. Render one smoky frame
at several values and count the grey pixels (smoke reads as mid grey, clearly
not white background and not the black of dense soot).

    python3 smoke_sweep.py
"""
import os, shutil, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np
from PIL import Image

# import the shared renderer with wick4 selected; it lives in experiment 07
sys.path.insert(0, os.path.join(_d, "experiments", "07_wick3_house_ignition"))
sys.argv = [sys.argv[0], "wick4", "wick4", "20,40,60,80,100,120,160,200,240,280,300"]
from ign_colour_render import (CASE, SMV, SMV_FILE, SMV_KEEP, ZOOM_INI,  # noqa
                               frame_colours, variant_smv)
import json

T = 160
state = json.load(open(os.path.join(CASE, "ign_state.json")))
variant_smv(frame_colours(state[str(T)]), SMV_FILE)

out = os.path.join(CASE, "smokesweep")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)

for v in (300, 900, 1800, 3600):
    body = "RENDERDIR\n smokesweep\nUNLOADALL\nLOADINIFILE\n %s\n" % os.path.basename(ZOOM_INI)
    for f in ("wick4_1_1.s3d", "wick4_1_3.s3d", "wick4_1.prt5"):
        body += "LOADFILE\n %s\n" % f
    body += "SETVIEWPOINT\n iso_b\nSMOKEPROP\n %g\n" % v
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n sw_%04d\n" % (T, v)
    open(os.path.join(CASE, "wick4.ssf"), "w").write(body)
    subprocess.run([SMV, "-runscript", "wick4"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=2400)
    p = os.path.join(out, "sw_%04d.png" % v)
    if not os.path.exists(p):
        print("SMOKEPROP %-6g NO FRAME" % v)
        continue
    a = np.asarray(Image.open(p).convert("RGB"), int)[:446]
    grey = (a.std(axis=2) < 8) & (a.min(axis=2) > 60) & (a.max(axis=2) < 240)
    white = a.min(axis=2) > 245
    print("SMOKEPROP %-6g grey (smoke) %6d px   background %6d px"
          % (v, int(grey.sum()), int(white.sum())))

shutil.copy(SMV_KEEP, SMV_FILE)
