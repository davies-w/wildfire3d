"""Render the wick3c animation with ONE smokeview process per pass.

Previously each frame launched its own smokeview instance, so a two-pass
animation started and quit the GUI app 20 times -- the source of the macOS
"app quitting" and window-context warnings.  The script language accepts
repeated SETTIMEVAL / RENDERONCE pairs, so one process renders every frame.

Pass 1 renders flame volume + firebrands; pass 2 renders soot.  They are then
blended so smoke does not wash out the fire, and assembled into a gif.
"""
import os, shutil, subprocess

CASE = os.path.expanduser("~/FDS/cases/wick3")
SMV = os.path.expanduser("~/FDS/bin/smv_quiet")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")
TIMES = [40, 90, 140, 180, 200, 220, 240, 260, 280, 300, 320, 350]

# smokeview auto-loads <casename>.ini, so give the new chid the known viewpoint
ini = os.path.join(CASE, "wick3.ini")
if os.path.exists(ini) and not os.path.exists(os.path.join(CASE, "wick3c.ini")):
    shutil.copy(ini, os.path.join(CASE, "wick3c.ini"))


def render(sub, files, prefix, hide_smoke):
    out = os.path.join(CASE, sub)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    body = "UNLOADALL\nLOADINIFILE\n wick3c.ini\n"
    for f in files:
        body += "LOADFILE\n %s\n" % f
    if hide_smoke:
        body += "SMOKEPROP\n 0.00001\n"
    body += "SETVIEWPOINT\n iso_b\n"
    for t in TIMES:                      # all frames, one process
        body += "SETTIMEVAL\n %d.0\nRENDERONCE\n %s_%03d\n" % (t, prefix, t)
    open(os.path.join(CASE, "wick3c.ssf"), "w").write("RENDERDIR\n %s\n" % sub + body)
    p = subprocess.run([SMV, "-runscript", "wick3c"], cwd=CASE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=2400)
    got = sorted(os.listdir(out))
    print("  %-9s exit %s  %d/%d frames" % (sub, p.returncode, len(got), len(TIMES)))


print("rendering (2 smokeview launches total):")
render("fire", ["wick3c_1_3.s3d", "wick3c_1.prt5"], "f", False)
render("smoke", ["wick3c_1_1.s3d"], "s", True)

from PIL import Image
import numpy as np

comp = os.path.join(CASE, "composited")
shutil.rmtree(comp, ignore_errors=True)
os.makedirs(comp)
n = 0
for t in TIMES:
    pf = os.path.join(CASE, "fire", "f_%03d.png" % t)
    ps = os.path.join(CASE, "smoke", "s_%03d.png" % t)
    if not (os.path.exists(pf) and os.path.exists(ps)):
        continue
    A = np.asarray(Image.open(pf).convert("RGB"), dtype=float)
    B = np.asarray(Image.open(ps).convert("RGB"), dtype=float)
    Image.fromarray(np.clip(0.80 * A + 0.20 * B, 0, 255).astype(np.uint8)).save(
        os.path.join(comp, "c_%03d.png" % t))
    n += 1
print("  composited", n, "frames")
subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"), comp,
                os.path.join(CASE, "wick3c_clean.gif"), "1.0"], check=False)
g = os.path.join(CASE, "wick3c_clean.gif")
print("gif:", os.path.getsize(g) if os.path.exists(g) else "FAILED")
