#!/usr/bin/env python3
"""Animate the BURNING RATE overlay -- the combustion-status view.

This is the "red patch where surfaces are too hot" visualisation: FDS only
gives a surface a nonzero burning rate after it passes its own
IGNITION_TEMPERATURE, so warm colours mark surfaces that have ignited and blue
marks surfaces that are safe.

The soot volume is loaded only to define the time array, then SMOKEPROP makes
it effectively invisible so the building surfaces are not obscured.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, VENV, VENV_PY  # noqa: E402

import os
import subprocess

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = VENV_PY
SSF = os.path.join(CASE, "garden_tall.ssf")

TPL = """RENDERDIR
 burnanim
UNLOADALL
LOADINIFILE
 garden_tall.ini
LOADFILE
 garden_tall_1_1.s3d
SMOKEPROP
 0.00001
LOADFILE
 garden_tall_1_2.bf
SETVIEWPOINT
 iso_b
SETTIMEVAL
 {t}
RENDERONCE
 b_{tag}
"""

out = os.path.join(CASE, "burnanim")
os.makedirs(out, exist_ok=True)
times = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
for t in times:
    tag = f"{t:03d}"
    open(SSF, "w").write(TPL.format(t=f"{t}.0", tag=tag))
    subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=900)

n = len([f for f in os.listdir(out) if f.endswith(".png")])
print(f"frames: {n}/{len(times)}")
subprocess.run([VENV, os.path.join(FDS_ROOT, "make_gif.py"), out,
                os.path.join(CASE, "burning_status.gif"), "1.0"], check=False)
g = os.path.join(CASE, "burning_status.gif")
print(f"gif: {os.path.getsize(g)} bytes" if os.path.exists(g) else "gif FAILED")
subprocess.run(["open", g], check=False)
