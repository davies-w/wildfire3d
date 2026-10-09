#!/usr/bin/env python3
"""Make the smoke invisible so the building surfaces are visible.

The soot volume is loaded only to define a global time array (SETTIMEVAL needs
one, and boundary files do not provide it).  SMOKEPROP sets the smoke mass
extinction coefficient, so a tiny value should render the soot effectively
invisible while keeping the time axis.
"""
import os
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
SSF = os.path.join(CASE, "garden_tall.ssf")

script = """RENDERDIR
 risk
UNLOADALL
LOADINIFILE
 garden_tall.ini
LOADFILE
 garden_tall_1_1.s3d
SMOKEPROP
 0.00001
LOADFILE
 garden_tall_1_1.bf
SETVIEWPOINT
 iso_b
SETTIMEVAL
 60.0
RENDERONCE
 clear_{tag}
"""

os.makedirs(os.path.join(CASE, "risk"), exist_ok=True)
open(SSF, "w").write(script.format(tag="smoke"))
r = subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                   capture_output=True, text=True,
                   stdin=subprocess.DEVNULL, timeout=900)
png = os.path.join(CASE, "risk", "clear_smoke.png")
print(f"exit={r.returncode} rendered={os.path.exists(png)}")
for line in (r.stdout + r.stderr).split("\n"):
    if "rror" in line or "not defined" in line:
        print("   ", line.strip())
