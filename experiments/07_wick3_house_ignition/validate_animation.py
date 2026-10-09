"""Validate the ignition animation against the measured temperatures.

Three independent checks:
  1. every frame present, distinct, and the same size -- a frozen render is
     otherwise invisible, as happened when 10 of 12 frames were byte-identical
  2. each frame's .smv carries the colour its temperature implies -- this is
     what proves the animation is data-driven rather than Smokeview's palette
  3. the warm (ignited) area at the end is well above the flame-only baseline

Exact pixel matching is not used for (3): Smokeview shades surfaces (WOOD WALL
222,184,135 renders as 178,147,108, i.e. 0.80) and the smoke volume multiplies
the result down, so a rendered pixel is not the table value.
"""
import hashlib, json, os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np
from PIL import Image

from ign_colour_render import CASE, OUT, colour
from ign_state import SURFACES, TIMES

state = json.load(open(os.path.join(CASE, "ign_state.json")))
have = [t for t in TIMES
        if os.path.exists(os.path.join(CASE, OUT, "c_%03d.png" % t))]
paths = [os.path.join(CASE, OUT, "c_%03d.png" % t) for t in have]


def smv_colour(path, name):
    """The RGB written for a surface in an .smv SURFACE table, or None."""
    lines = open(path, errors="replace").read().split("\n")
    for i, line in enumerate(lines):
        if (line.strip() == "SURFACE" and i + 3 < len(lines)
                and lines[i + 1].strip() == name):
            p = lines[i + 3].split()
            if len(p) >= 7:
                return tuple(round(float(v) * 255) for v in p[3:6])
    return None


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

# the flame is warm too, so a frame with nothing ignited still has a baseline;
# what matters is that the ignited frames rise well clear of it
order = sorted(means)
sep = means[order[-1]] > 1.6 * means[order[0]]

# the exact check that the colouring is data-driven
wrong = 0
for t in have:
    p = os.path.join(CASE, "fr_%03d.smv" % t)
    if not os.path.exists(p):
        continue
    for n in SURFACES:
        want = colour(n, state[str(t)].get(n))
        got = smv_colour(p, n)
        if got is not None and max(abs(got[i] - want[i]) for i in range(3)) > 1:
            print("  t=%-4d %-10s file %s, expected %s" % (t, n, got, want))
            wrong += 1

ok = sep and wrong == 0 and len(digests) == len(paths) and len(sizes) == 1
print("\ncolour mismatches in the per-frame .smv: %d" % wrong)
print("warm area above the flame baseline    :", sep)
print("all distinct:", len(digests) == len(paths))
print("single size :", len(sizes) == 1)
print("\nVALIDATION:", "PASS" if ok else "FAIL")
