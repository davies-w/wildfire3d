"""Blend the ignition-state animation: normal colours, orange/red once burning.

Pass A (norm) has no boundary file, so objects show their geometry colours.
Pass B (burn) draws the BURNING RATE boundary file, which is zero until a
surface passes its own IGNITION_TEMPERATURE.  Warm pixels in B therefore mark
ignited surfaces, and are washed orange/red over A.

The colourbar exists only in B (A has no boundary file), so it would otherwise
be detected as "warm and changed" and painted onto the image -- the salmon
block outside the render box reported earlier.  It is detected as columns where
A is background-white but B is strongly coloured, and excluded.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, VENV, VENV_PY  # noqa: E402

import os, subprocess

import numpy as np
from PIL import Image

CASE = os.path.join(FDS_ROOT, "cases/wick3")
VENV = VENV_PY
TIMES = [40, 90, 140, 180, 200, 220, 240, 260, 280, 300, 320, 350]
HOT = np.array([235.0, 70.0, 20.0])

out = os.path.join(CASE, "ignition_clean")
os.makedirs(out, exist_ok=True)
n = 0
for t in TIMES:
    pa = os.path.join(CASE, "norm", "n_%03d.png" % t)
    pb = os.path.join(CASE, "burn", "b_%03d.png" % t)
    if not (os.path.exists(pa) and os.path.exists(pb)):
        continue
    A = np.asarray(Image.open(pa).convert("RGB"), dtype=float)
    B = np.asarray(Image.open(pb).convert("RGB"), dtype=float)
    # colourbar: background in A, strongly coloured in B
    whiteA = (A.min(axis=2) > 235)
    colB = (B.max(axis=2) - B.min(axis=2)) > 40
    cbar = (whiteA & colB).mean(axis=0) > 0.20
    warm = np.clip((B[:, :, 0] - B[:, :, 2] - 20.0) / 120.0, 0, 1)
    moved = (np.abs(B - A).max(axis=2) > 25).astype(float)
    m = (warm * moved)[..., None]
    m[:, cbar, :] = 0.0
    # never paint the background: the scene renders as pure white where there is
    # no geometry, so any "warm" reading there is a pass-to-pass rendering
    # difference, not a burning surface.  This is what produced the salmon quad
    # outside the render box.
    m[whiteA] = 0.0
    img = np.clip(A * (1 - m) + HOT * m, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(out, "i_%03d.png" % t))
    n += 1
    if t == 280:
        print("  colourbar columns excluded:", int(cbar.sum()))
print("blended", n, "frames")
subprocess.run([VENV, os.path.join(FDS_ROOT, "make_gif.py"), out,
                os.path.join(CASE, "ignition_clean.gif"), "1.0"], check=False)
g = os.path.join(CASE, "ignition_clean.gif")
print("gif:", os.path.getsize(g) if os.path.exists(g) else "FAILED")
