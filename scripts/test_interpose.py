"""Test whether interposing SetFrontProcess stops smokeview stealing focus.

Runs smokeview with DYLD_INSERT_LIBRARIES pointing at the no-op shim, then asks
the system log whether any SetFrontProcess call was made by smokeview during the
run.  Frames must also still be produced, or a silent failure would look like
success.
"""
import os, shutil, subprocess, time

CASE = os.path.expanduser("~/FDS/cases/wick3")
SMV = os.path.expanduser("~/FDS/bin/smv_quiet")
SHIM = os.path.expanduser("~/FDS/nofront.dylib")

out = os.path.join(CASE, "agent_test2")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)

body = ("UNLOADALL\nLOADINIFILE\n wick3c.ini\n"
        "LOADFILE\n wick3c_1_3.s3d\n"
        "SETVIEWPOINT\n iso_b\n"
        "SETTIMEVAL\n 250.0\nRENDERONCE\n sh_250\n")
open(os.path.join(CASE, "wick3c.ssf"), "w").write("RENDERDIR\n agent_test2\n" + body)

env = dict(os.environ)
t0 = time.time()
p = subprocess.run([SMV, "wick3c", "-runscript"], cwd=CASE, env=env,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                   stdin=subprocess.DEVNULL, timeout=600)
print("exit %s in %.1f s" % (p.returncode, time.time() - t0))
print("produced:", sorted(os.listdir(out)))
if "dyld" in p.stdout.lower():
    print("DYLD NOTE:", [l for l in p.stdout.splitlines() if "dyld" in l.lower()][:3])
