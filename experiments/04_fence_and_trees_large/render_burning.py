#!/usr/bin/env python3
"""Render the BURNING RATE boundary file -- FDS's own combustion indicator.

FDS gives a surface a nonzero burning rate only once it passes its own
IGNITION_TEMPERATURE, and each material has its own value (glass 180 C, wood
350 C, roof 550 C).  So this output already encodes per-material combustion,
which one global colorbar threshold could not express.

Non-burning surfaces sit at 0 (cold colour); anything burning is warm.
"""
import os
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
SSF = os.path.join(CASE, "garden_tall.ssf")

TPL = """RENDERDIR
 risk
UNLOADALL
LOADINIFILE
 garden_tall.ini
LOADFILE
 garden_tall_1_1.s3d
SMOKEPROP
 0.00001
LOADFILE
 garden_tall_1_2.bf
SETVIEWPOINT
 iso_b
SETTIMEVAL
 {t}
RENDERONCE
 burn_{tag}
"""

os.makedirs(os.path.join(CASE, "risk"), exist_ok=True)
for tag in ("040", "060", "090"):
    open(SSF, "w").write(TPL.format(t=f"{int(tag)}.0", tag=tag))
    r = subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                       capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=900)
    png = os.path.join(CASE, "risk", f"burn_{tag}.png")
    print(f"t={tag}: exit={r.returncode} rendered={os.path.exists(png)}")
    for line in (r.stdout + r.stderr).split("\n"):
        if "rror" in line or "not defined" in line:
            print("   ", line.strip())
