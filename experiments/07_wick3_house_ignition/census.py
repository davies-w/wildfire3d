"""What colours are actually in the rendered frames?

The validator assumed the .smv colours (shaded) appear in the pixels. They do
not, so measure the real palette rather than guess again: the most common
colours, beside the intended surface colours for the same frame.
"""
import json, os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np
from PIL import Image

from ign_colour_render import CASE, OUT, colour
from ign_state import SURFACES

state = json.load(open(os.path.join(CASE, "ign_state.json")))

for t in (40, 300):
    p = os.path.join(CASE, OUT, "c_%03d.png" % t)
    a = np.asarray(Image.open(p).convert("RGB"), int)
    cols, counts = np.unique(a.reshape(-1, 3), axis=0, return_counts=True)
    order = np.argsort(-counts)
    print("=== t=%d  (%d x %d) ===" % (t, a.shape[1], a.shape[0]))
    print("intended:")
    for n in SURFACES:
        print("   %-10s %s" % (n, colour(n, state[str(t)].get(n))))
    print("most common actual colours:")
    for i in order[:10]:
        print("   %-16s %6d px" % (tuple(int(v) for v in cols[i]), counts[i]))
    print()
