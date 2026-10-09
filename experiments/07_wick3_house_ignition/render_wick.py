"""Render the wick case: embers + flame + smoke + house temperature together.

pass 1  flame volume + particles + house-only boundary file  -> fireembers/
pass 2  soot volume                                          -> smoke/
blend   0.80*pass1 + 0.20*pass2                               -> composited/

One frame per Smokeview invocation: multi-frame runs of the large volume files
crash intermittently.  The flame volume doubles as the time axis that
SETTIMEVAL needs.
"""
import os
import shutil
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")
TIMES = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150]


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
    n = len(os.listdir(out))
    print(f"  {subdir}: {n}/{len(TIMES)}")
    return n


render("fireembers", ["wick_1_3.s3d", "wick_1.prt5", "wick_1_1.bf"], "ft")
render("smoke", ["wick_1_1.s3d"], "s")

subprocess.run([VENV, os.path.expanduser("~/FDS/composite_smoke.py"),
                os.path.join(CASE, "fireembers"), os.path.join(CASE, "smoke"),
                os.path.join(CASE, "composited"), "0.80"], check=False)
subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"),
                os.path.join(CASE, "composited"),
                os.path.join(CASE, "wick.gif"), "1.0"], check=False)
g = os.path.join(CASE, "wick.gif")
print("gif:", os.path.getsize(g) if os.path.exists(g) else "FAILED")
subprocess.run(["open", g], check=False)
