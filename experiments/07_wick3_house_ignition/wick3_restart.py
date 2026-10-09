"""Build a restart case: continue wick3 from t=200 to t=400.

&RESTART?  No -- the switch is RESTART=T on the MISC line (found in
Examples/Restart/geom_restart_a.fds).  FDS then reads <CHID>.restart, which
wick3 wrote every DT_RESTART=30 s.

Nothing else may change: the manual states that across a stop/restart you can
only alter parameters that do not change the size of runtime arrays.  T_END is
fine; geometry is not.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import re

CASE = os.path.join(FDS_ROOT, "cases/wick3")
src = os.path.join(CASE, "wick3.fds")
s = open(src).read()

s = s.replace("T_END=200.", "T_END=400.")
s = re.sub(r"&MISC ", "&MISC RESTART=.TRUE., ", s, count=1)

open(os.path.join(CASE, "wick3_restart.fds"), "w").write(s)
print([l for l in s.split("\n") if l.startswith("&MISC")])
print([l for l in s.split("\n") if l.startswith("&TIME")])
print("restart file present:", os.path.exists(os.path.join(CASE, "wick3_1.restart")))
