"""Read the ladder tree's surface history from the clean wick3c run.

The render suggests the big canopy beside the house is not igniting, while the
wild trees across the garden are.  That is backwards from expectation, so it
needs measuring rather than eyeballing.

fds2ascii selects boundary data by face orientation and lists the patches it
finds per orientation.  This dumps the listing first so the canopy's patch can
be identified by its bounding box, then extracts values for the patches of
interest: the canopy (x 14.5-17.5) and, for reference, the house west wall.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, re, subprocess

CASE = os.path.join(FDS_ROOT, "cases/wick3")
F2A = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/bin/fds2ascii")
T0, T1 = 300, 302


def run(orient, var, tag):
    out = "probe_%s.txt" % tag
    stdin = "wick3c\n3\n1\nn\n%d %d\n%d\n1\n%d\n%s\n" % (T0, T1, orient, var, out)
    subprocess.run([F2A], cwd=CASE, input=stdin, text=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
    path = os.path.join(CASE, out)
    return path if os.path.exists(path) else None


for orient in (1, -1, 2, -2, 3, -3):
    p = run(orient, 1, "o%+d" % orient)
    if not p:
        print("orientation %+d: no output" % orient)
        continue
    print("=== orientation %+d ===" % orient)
    cur = None
    n = 0
    for line in open(p):
        if line.startswith("Patch"):
            if cur:
                print("    %d values" % n)
            cur = line.strip()
            n = 0
            print("  %s" % cur)
        elif cur and line.strip() and "," in line:
            n += 1
    if cur:
        print("    %d values" % n)
