"""Render any animation frames that are missing.

Smokeview segfaulted (exit -11) rendering t=200 while the other 11 frames
succeeded, so a single crash was silently costing a frame.  This re-renders
only what is absent and reports the exit code, so a repeat crash is visible
rather than quiet.
"""
import json, os, shutil, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from ign_state import TIMES  # noqa: E402
from ign_colour_render import (BASE, CASE, OUT, SMV_FILE, SMV_KEEP,  # noqa: E402
                               colour, patch_smv, render_frame)

state = json.load(open(os.path.join(CASE, "ign_state.json")))
missing = [t for t in TIMES
           if not os.path.exists(os.path.join(CASE, OUT, "c_%03d.png" % t))]

if not missing:
    print("no missing frames")
    sys.exit(0)

print("missing:", ", ".join(str(t) for t in missing))
for t in missing:
    temps = state[str(t)]
    patch_smv({n: colour(n, temps.get(n)) for n in BASE})
    rc = render_frame(t, "c_%03d" % t)
    ok = os.path.exists(os.path.join(CASE, OUT, "c_%03d.png" % t))
    print("  t=%-4d exit %-4s frame %s" % (t, rc, "written" if ok else "MISSING"))

shutil.copy(SMV_KEEP, SMV_FILE)
