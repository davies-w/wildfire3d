"""Test whether the agent-wrapped smokeview renders without stealing focus.

Launches via `open -g -W -a <bundle> --args ...`.  -g means "do not bring to
foreground"; the bundle's LSUIElement=true makes it an agent app.  Success is
measured by whether the PNGs appear.
"""
import os, shutil, subprocess, time

CASE = os.path.expanduser("~/FDS/cases/wick3")
APP = os.path.expanduser("~/FDS/apps/SmokeviewAgent.app/Contents/MacOS/smokeview-launch")
TIMES = [100, 250, 350]

out = os.path.join(CASE, "agent_test")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)

body = ("UNLOADALL\nLOADINIFILE\n wick3c.ini\n"
        "LOADFILE\n wick3c_1_3.s3d\nLOADFILE\n wick3c_1.prt5\n"
        "SETVIEWPOINT\n iso_b\n")
for t in TIMES:
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n ag_%03d\n" % (t, t)
open(os.path.join(CASE, "wick3c.ssf"), "w").write("RENDERDIR\n agent_test\n" + body)

t0 = time.time()
p = subprocess.run([APP, "wick3c", "-runscript"], cwd=CASE,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                   stdin=subprocess.DEVNULL, timeout=900)
print("exit %s in %.1f s" % (p.returncode, time.time() - t0))
if p.stdout.strip():
    print("output:", p.stdout.strip()[:300])
print("produced:", sorted(os.listdir(out)))
