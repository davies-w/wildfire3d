"""Extract the house west wall temperature history from the clean wick3c run.

Patch 2 is the house west face (x=18, y 8..16, z 0..3.5), the surface the fence
spur attaches to.  For each time window this reports mean and max wall
temperature and how many cells exceed 350 C (wood ignition).

Output comes from fds2ascii, so no devices were needed in the input file.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, subprocess

CASE = os.path.join(FDS_ROOT, "cases/wick3")
F2A = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/bin/fds2ascii")
WINDOWS = [48, 100, 148, 200, 248, 300, 348]
IGN = 350.0


def extract(t0):
    out = "wt_%03d.txt" % t0
    stdin = "wick3c\n3\n1\nn\n%d %d\n-1\n1\n1\n%s\n" % (t0, t0 + 2, out)
    subprocess.run([F2A], cwd=CASE, input=stdin, text=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=1200)
    path = os.path.join(CASE, out)
    if not os.path.exists(path):
        return None
    vals, seen = [], False
    for line in open(path):
        if line.startswith("Patch"):
            if seen:
                break
            seen = "18.00<x<  18.00" in line and "8.00<y<  16.00" in line
            continue
        if seen:
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    vals.append(float(parts[3]))
                except ValueError:
                    pass
    return vals


print("%6s %10s %10s %12s" % ("t (s)", "mean C", "max C", "cells>350C"))
for t0 in WINDOWS:
    v = extract(t0)
    if not v:
        print("%6d   no data" % t0)
        continue
    hot = sum(1 for x in v if x > IGN)
    print("%6d %10.1f %10.1f %7d/%d" % (t0, sum(v) / len(v), max(v), hot, len(v)))
