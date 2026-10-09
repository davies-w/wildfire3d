"""Render the small (32 x 24 m) wick3 scenario across the ignition window.

The run covers t = 0-400 s (200 s solve, then a restart to 400).  The house
west wall data says it crosses its 350 C ignition temperature between t = 200
and t = 300 s, reaching 949 C mean / 1410 C max by t = 300.

Frames are clustered around that window so the ignition is actually visible.

pass 1  flame volume + firebrands + boundary temperature -> fire/
pass 2  soot volume                                      -> smoke/
blend   0.80*pass1 + 0.20*pass2                           -> composited/
"""
import os
import shutil
import subprocess

CASE = os.path.expanduser("~/FDS/cases/wick3")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")
TIMES = [80, 140, 180, 210, 240, 270, 300, 330, 360, 390]


def render(subdir, files, prefix):
    out = os.path.join(CASE, subdir)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for t in TIMES:
        body = "".join(f"LOADFILE\n {f}\n" for f in files)
        open(os.path.join(CASE, "wick3.ssf"), "w").write(
            f"RENDERDIR\n {subdir}\nUNLOADALL\nLOADINIFILE\n wick3.ini\n"
            f"{body}SETVIEWPOINT\n iso_b\nSETTIMEVAL\n {t}.0\n"
            f"RENDERONCE\n {prefix}_{t:03d}\n")
        subprocess.run([SMV, "-runscript", "wick3"], cwd=CASE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=900)
    print(f"  {subdir}: {len(os.listdir(out))}/{len(TIMES)}")


render("fire", ["wick3_1_3.s3d", "wick3_1.prt5", "wick3_1_1.bf"], "ft")
render("smoke", ["wick3_1_1.s3d"], "s")

subprocess.run([VENV, os.path.expanduser("~/FDS/composite_smoke.py"),
                os.path.join(CASE, "fire"), os.path.join(CASE, "smoke"),
                os.path.join(CASE, "composited"), "0.80"], check=False)
subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"),
                os.path.join(CASE, "composited"),
                os.path.join(CASE, "wick3_fire.gif"), "0.8"], check=False)
g = os.path.join(CASE, "wick3_fire.gif")
print("gif:", os.path.getsize(g) if os.path.exists(g) else "FAILED")
subprocess.run(["open", g], check=False)
