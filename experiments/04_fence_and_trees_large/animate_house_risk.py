import os
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")

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

out = os.path.join(CASE, "hr")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))

for t in (20, 30, 40, 50, 60, 70, 80, 90, 100, 110):
    tag = f"{t:03d}"
    open(os.path.join(CASE, "house_risk.ssf"), "w").write(
        TPL.format(t=f"{t}.0", tag=tag))
    subprocess.run([SMV, "-runscript", "house_risk"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=900)

n = len([f for f in os.listdir(out) if f.endswith(".png")])
print("frames", n)
subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"), out,
                os.path.join(CASE, "house_risk.gif"), "1.0"], check=False)
g = os.path.join(CASE, "house_risk.gif")
print("gif", os.path.getsize(g) if os.path.exists(g) else "FAILED")
subprocess.run(["open", g], check=False)
