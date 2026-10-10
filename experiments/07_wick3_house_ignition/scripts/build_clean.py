"""Build the clean, single-run solve of the small wick case.

CHID='wick3c' so the restart-contaminated wick3 output is left intact.
T_END=350 s -- long enough for ignition, about an hour of wall time.

RESTART is NOT set, so every output file gets one unambiguous time axis.
DT_RESTART stays on purely as insurance; no restart is actually performed.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os

CASE = os.path.join(FDS_ROOT, "cases/wick3")
s = open(os.path.join(CASE, "wick3.fds")).read()
s = s.replace("CHID='wick3'", "CHID='wick3c'")
s = s.replace("T_END=200.", "T_END=350.")
open(os.path.join(CASE, "wick3c.fds"), "w").write(s)

print([l for l in s.split("\n") if l.startswith("&TIME")])
print([l for l in s.split("\n") if l.startswith("&MESH")])
print([l for l in s.split("\n") if l.startswith("&DUMP")])
print("RESTART set:", "RESTART" in s)
