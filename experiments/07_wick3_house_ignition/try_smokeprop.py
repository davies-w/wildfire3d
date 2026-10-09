"""How much of the ignition colour survives the smoke at t=300?

At t=300 every surface is above its ignition temperature, so the frame should
show the scene in orange-red.  Measured, it is dominated by near-black: the soot
volume is drawn in front and multiplies the surface colour down.

Sweep the extinction coefficient at t=300 and count pixels reading as warm
(red clearly above blue), which is the quantity of interest.
"""
import json, os, shutil, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np
from PIL import Image

from ign_colour_render import (CASE, SMV, SMV_FILE, SMV_KEEP, VOLUMES,
                               ZOOM_INI, ZOOM_LINE, frame_colours, variant_smv)

state = json.load(open(os.path.join(CASE, "ign_state.json")))
T = 300
variant_smv(frame_colours(state[str(T)]), SMV_FILE)
open(ZOOM_INI, "w").write(ZOOM_LINE)

out = os.path.join(CASE, "smokesweep")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)

for v in (2500, 1200, 600, 300, 0):
    body = "RENDERDIR\n smokesweep\nUNLOADALL\nLOADINIFILE\n wick3c.ini\n"
    for f in VOLUMES:
        body += "LOADFILE\n %s\n" % f
    body += "SETVIEWPOINT\n iso_b\n"
    body += "LOADINIFILE\n %s\n" % os.path.basename(ZOOM_INI)
    body += "SMOKEPROP\n %g\n" % v
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n sw_%04d\n" % (T, v)
    open(os.path.join(CASE, "wick3c.ssf"), "w").write(body)
    subprocess.run([SMV, "-runscript", "wick3c"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=2400)

    p = os.path.join(out, "sw_%04d.png" % v)
    if not os.path.exists(p):
        print("SMOKEPROP %-6g NO FRAME" % v)
        continue
    a = np.asarray(Image.open(p).convert("RGB"), int)[:446]
    warm = (a[:, :, 0] - a[:, :, 2] > 40) & (a[:, :, 0] > 60)
    dark = a.max(axis=2) < 25
    print("SMOKEPROP %-6g warm %6d px   near-black %6d px"
          % (v, int(warm.sum()), int(dark.sum())))

shutil.copy(SMV_KEEP, SMV_FILE)
