"""Render one frame of each case at several smoke coefficients, for comparison.

SMOKEPROP is a display parameter, not physics: it sets the soot mass extinction
coefficient used to draw the smoke volume.  If it differs between two cases,
their animations are not comparable, because the plume density on screen is
partly the setting rather than the fire.  So the choice is made by looking.

    python3 smokeprop_sweep.py <outdir> <v1,v2,...> <cfg:time> [cfg:time ...]
"""
import os, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
HERE = _d
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

outdir = os.path.abspath(sys.argv[1])
values = sys.argv[2].split(",")
cases = [a.rsplit(":", 1) for a in sys.argv[3:]]
os.makedirs(outdir, exist_ok=True)

for cfg, t in cases:
    tag = os.path.basename(os.path.dirname(os.path.abspath(cfg)))[:2]
    for v in values:
        out = os.path.join(outdir, "%s_t%s_sm%s.png" % (tag, t, v))
        subprocess.run([sys.executable, os.path.join(HERE, "render_view.py"),
                        cfg, t, "iso_b", out, v], timeout=2400)
        print(out, "ok" if os.path.exists(out) else "MISSING")
