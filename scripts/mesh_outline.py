"""Measure the mesh boundary box Smokeview draws, to judge removability.

Smokeview has no script command for the mesh outline: the `o` key cycles
1 current mesh / 2 whole case / 3 none, but sending it via KEYBOARD in a batch
run has no effect (verified -- three presses changed nothing).  So the only
route is to remove the lines from the rendered pixels, which is only safe if
they are thin, and darker than anything else in the frame.

This reports, for one frame: how dark the darkest pixels are, how wide the
runs of them are, and how much of the frame is that dark at all.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np
from PIL import Image

if len(sys.argv) < 2:
    sys.exit("usage: mesh_outline.py <frame.png>")
a = np.asarray(Image.open(sys.argv[1]).convert("RGB"), int)
dark = a.max(axis=2)

print("%s  %d x %d" % (sys.argv[1], a.shape[1], a.shape[0]))
for t in (10, 40, 80, 140, 200):
    n = int((dark < t).sum())
    print("  max-channel < %-3d : %6d px  (%.2f%%)" % (t, n, 100.0 * n / dark.size))

# run lengths of very dark pixels along rows, to see how thick the lines are
row = dark < 40
runs = []
for r in row:
    n = 0
    for v in r:
        if v:
            n += 1
        elif n:
            runs.append(n)
            n = 0
print("\ndark run lengths along rows: %s" % sorted(set(runs))[:12])
print("total dark runs: %d" % len(runs))
