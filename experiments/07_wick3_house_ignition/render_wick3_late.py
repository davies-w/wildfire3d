"""Render the CONTINUATION range (t = 240 to 400) for wick3."""
import os
import shutil
import subprocess

CASE = os.path.expanduser("~/FDS/cases/wick3")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")
TIMES = [240, 280, 320, 360, 400]


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


render("late", ["wick3_1_3.s3d", "wick3_1.prt5", "wick3_1_1.bf"], "l")

subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"),
                os.path.join(CASE, "late"),
                os.path.join(CASE, "wick3_late.gif"), "0.8"], check=False)
g = os.path.join(CASE, "wick3_late.gif")
print("gif:", os.path.getsize(g) if os.path.exists(g) else "FAILED")
subprocess.run(["open", os.path.join(CASE, "late", "l_400.png")], check=False)
