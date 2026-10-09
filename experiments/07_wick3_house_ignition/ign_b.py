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
TIMES = [80, 140, 180, 210, 240, 270, 300, 330, 360, 390]
HOT = np.array([235.0, 70.0, 20.0])

out = os.path.join(CASE, "ignition")
os.makedirs(out, exist_ok=True)
n = 0
for t in TIMES:
    pa = os.path.join(CASE, "normal", "n_%03d.png" % t)
    pb = os.path.join(CASE, "burnmask", "b_%03d.png" % t)
    if not (os.path.exists(pa) and os.path.exists(pb)):
        continue
    A = np.asarray(Image.open(pa).convert("RGB"), dtype=float)
    B = np.asarray(Image.open(pb).convert("RGB"), dtype=float)
    # burning surfaces are warm in B; non-burning sit at the colorbar minimum
    warm = np.clip((B[:, :, 0] - B[:, :, 2] - 20.0) / 120.0, 0, 1)
    # only where B departs from A, so static geometry is never misread
    moved = (np.abs(B - A).max(axis=2) > 25).astype(float)
    m = (warm * moved)[..., None]
    img = np.clip(A * (1 - m) + HOT * m, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(out, "i_%03d.png" % t))
    n += 1
print("frames", n)
subprocess.run([VENV, os.path.join(FDS_ROOT, "make_gif.py"), out,
                os.path.join(CASE, "ignition.gif"), "0.8"], check=False)
g = os.path.join(CASE, "ignition.gif")
print("gif", os.path.getsize(g) if os.path.exists(g) else "FAILED")
subprocess.run(["open", g], check=False)
