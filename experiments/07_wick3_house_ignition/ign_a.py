import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, shutil, subprocess

CASE = os.path.join(FDS_ROOT, "cases/wick3")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
TIMES = [80, 140, 180, 210, 240, 270, 300, 330, 360, 390]

def render(sub, files, pre, hide=False):
    out = os.path.join(CASE, sub)
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    for t in TIMES:
        body = "".join("LOADFILE\n %s\n" % f for f in files)
        k = "SMOKEPROP\n 0.00001\n" if hide else ""
        open(os.path.join(CASE, "wick3.ssf"), "w").write(
            "RENDERDIR\n %s\nUNLOADALL\nLOADINIFILE\n wick3.ini\n%s%s"
            "SETVIEWPOINT\n iso_b\nSETTIMEVAL\n %s.0\nRENDERONCE\n %s_%03d\n"
            % (sub, body, k, t, pre, t))
        subprocess.run([SMV, "-runscript", "wick3"], cwd=CASE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=900)
    print(sub, len(os.listdir(out)), "/", len(TIMES))

render("normal", ["wick3_1_3.s3d", "wick3_1.prt5"], "n")
render("burnmask", ["wick3_1_1.s3d", "wick3_1_2.bf"], "b", hide=True)
