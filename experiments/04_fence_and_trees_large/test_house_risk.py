import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import subprocess

CASE = os.path.join(FDS_ROOT, "cases/garden_tall")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")

TPL = """RENDERDIR
 hr
UNLOADALL
LOADINIFILE
 garden_tall.ini
LOADFILE
 house_risk_1_3.s3d
LOADFILE
 house_risk_1.prt5
LOADFILE
 house_risk_1_1.bf
SETVIEWPOINT
 iso_b
SETTIMEVAL
 {t}
RENDERONCE
 hr_{tag}
"""

os.makedirs(os.path.join(CASE, "hr"), exist_ok=True)
open(os.path.join(CASE, "house_risk.ssf"), "w").write(TPL.format(t="60.0", tag="060"))
r = subprocess.run([SMV, "-runscript", "house_risk"], cwd=CASE,
                   capture_output=True, text=True,
                   stdin=subprocess.DEVNULL, timeout=900)
png = os.path.join(CASE, "hr", "hr_060.png")
print("exit", r.returncode, "rendered", os.path.exists(png))
for l in (r.stdout + r.stderr).split("\n"):
    if "rror" in l or "not defined" in l or "Loading" in l:
        print("  ", l.strip())
