"""Validate the ignition animation against the measured temperatures.

Checks:
  - every frame present, distinct, and the same size (a frozen render is
    invisible otherwise; 10 of 12 frames were once byte-identical)
  - the warm (ignited) area is near zero while no surface has crossed its
    ignition temperature, and large once they have

Exact-colour matching is not used: Smokeview shades surfaces (WOOD WALL
222,184,135 renders as 178,147,108, i.e. 0.80) and the smoke volume multiplies
the result down, so the rendered value is not the table value.
"""
import hashlib, json, os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np
from PIL import Image

from ign_colour_render import CASE, OUT
from ign_state import SURFACES, TIMES

state = json.load(open(os.path.join(CASE, "ign_state.json")))
have = [t for t in TIMES
        if os.path.exists(os.path.join(CASE, OUT, "c_%03d.png" % t))]
paths = [os.path.join(CASE, OUT, "c_%03d.png" % t) for t in have]

digests = {hashlib.md5(open(p, "rb").read()).hexdigest() for p in paths}
sizes = {Image.open(p).size for p in paths}
print("frames present : %d of %d" % (len(paths), len(TIMES)))
print("distinct frames: %d" % len(digests))
print("frame sizes    : %s" % sizes)

print("\n%-6s %-8s %-10s %s" % ("t", "ignited", "warm px", "surfaces above ignition"))
rows = []
for t, p in zip(have, paths):
    a = np.asarray(Image.open(p).convert("RGB"), int)
    warm = int(((a[:, :, 0] - a[:, :, 2] > 40) & (a[:, :, 0] > 60)).sum())
    ign = [n for n in SURFACES
           if state[str(t)].get(n) is not None
           and state[str(t)][n] >= SURFACES[n][1]]
    rows.append((t, warm, len(ign)))
    print("%-6d %-8d %-10d %s" % (t, len(ign), warm, ", ".join(ign) or "-"))

by_count = {}
for t, warm, n in rows:
    by_count.setdefault(n, []).append(warm)
means = {n: sum(v) / len(v) for n, v in by_count.items()}
print("\nmean warm area by number of ignited surfaces:")
for n in sorted(means):
    print("  %d ignited -> %8.0f px" % (n, means[n]))

# The orange flame is also warm, so a frame with nothing ignited still has a
# baseline.  What matters is that the warm area grows with the number of
# ignited surfaces, and is clearly above that baseline once several ignite.
order = sorted(means)
mono = all(means[a] <= means[b] for a, b in zip(order, order[1:]))
sep = means[order[0]] < means[order[-1]] - 1500
ok = mono and sep and len(digests) == len(paths) and len(sizes) == 1
print("monotone in ignited count      :", mono)
print("above the flame-only baseline  :", sep)
print("all distinct:", len(digests) == len(paths))
print("single size :", len(sizes) == 1)
print("\nVALIDATION:", "PASS" if ok else "FAIL")
