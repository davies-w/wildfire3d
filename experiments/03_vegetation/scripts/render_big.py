"""Re-render the LARGE (60 x 60 m) wick scenario with temperature colours.

No re-solve: the existing wick_* output is used as-is.

pass 1  flame volume + firebrands + boundary temperature -> fireembers/
pass 2  soot volume                                      -> smoke/
blend   0.80*pass1 + 0.20*pass2                           -> composited/

Note: only surfaces with BNDF_OBST=.TRUE. carry temperature data -- the house
walls and roof, the four fence pieces and the ladder tree.  The five ordinary
garden trees have no boundary output, so they render in their static geometry
colours whatever they are doing.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, VENV, VENV_PY  # noqa: E402

import os
import shutil
import subprocess

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = VENV_PY
TIMES = [10, 20, 30, 40, 50, 60, 75, 90, 105, 120, 135, 150, 160]


def render(subdir, files, prefix):
    out = os.path.join(CASE, subdir)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for t in TIMES:
        body = "".join(f"LOADFILE\n {f}\n" for f in files)
        open(os.path.join(CASE, "wick.ssf"), "w").write(
            f"RENDERDIR\n {subdir}\nUNLOADALL\nLOADINIFILE\n wick.ini\n"
            f"{body}SETVIEWPOINT\n iso_b\nSETTIMEVAL\n {t}.0\n"
            f"RENDERONCE\n {prefix}_{t:03d}\n")
        subprocess.run([SMV, "-runscript", "wick"], cwd=CASE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=900)
    print(f"  {subdir}: {len(os.listdir(out))}/{len(TIMES)}")


render("bigfire", ["wick_1_3.s3d", "wick_1.prt5", "wick_1_1.bf"], "ft")
render("bigsmoke", ["wick_1_1.s3d"], "s")

subprocess.run([VENV, os.path.join(FDS_ROOT, "composite_smoke.py"),
                os.path.join(CASE, "bigfire"), os.path.join(CASE, "bigsmoke"),
                os.path.join(CASE, "bigcomposited"), "0.80"], check=False)
subprocess.run([VENV, os.path.join(FDS_ROOT, "make_gif.py"),
                os.path.join(CASE, "bigcomposited"),
                os.path.join(CASE, "wick_big.gif"), "0.7"], check=False)
g = os.path.join(CASE, "wick_big.gif")
print("gif:", os.path.getsize(g) if os.path.exists(g) else "FAILED")
subprocess.run(["open", g], check=False)
