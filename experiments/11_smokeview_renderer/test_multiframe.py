"""Test rendering several frames in ONE smokeview process.

The existing render scripts invoke smokeview once per frame, so each frame
launches and quits the GUI application.  That churn is what produces the macOS
"app quitting" and window-context warnings.  The script language supports
repeated SETTIMEVAL / RENDERONCE pairs, so one process should be able to render
the whole animation.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, shutil, subprocess, time

CASE = os.path.join(FDS_ROOT, "cases/wick3")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
TIMES = [80, 180, 300, 390]

body = ("UNLOADALL\nLOADINIFILE\n wick3.ini\n"
        "LOADFILE\n wick3_1_3.s3d\nLOADFILE\n wick3_1.prt5\n"
        "SETVIEWPOINT\n iso_b\n")
for t in TIMES:
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n mf_%03d\n" % (t, t)

d = os.path.join(CASE, "test_multiframe")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)
open(os.path.join(CASE, "wick3.ssf"), "w").write("RENDERDIR\n test_multiframe\n" + body)

t0 = time.time()
p = subprocess.run([SMV, "-runscript", "wick3"], cwd=CASE,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                   stdin=subprocess.DEVNULL, timeout=1800, text=True)
print("one process, %d frames: exit %s in %.1f s" % (len(TIMES), p.returncode, time.time() - t0))
print("produced:", sorted(os.listdir(d)))
