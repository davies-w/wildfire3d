"""Render one frame at several ZOOM settings, to find one that fits the scene.

Renders t=280 three ways:
  base     -- the case .ini as it is
  after    -- case .ini, then a ZOOM-only ini AFTER SETVIEWPOINT, so the zoom
              is applied on top of the viewpoint rather than being overwritten
  merged   -- a copy of the case .ini with a ZOOM line added

Which one actually changes the framing is not documented, so all three are
tried and measured with measure_framing.py.
"""
import os, shutil, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

CASE = os.path.join(FDS_ROOT, "cases/wick3")
SMV = os.path.join(FDS_ROOT, "bin/smv_quiet")
T = 280

# ZOOM takes an index, or a negative index plus an explicit amount.  Sweep the
# amount and keep the largest one that still leaves the scene inside the frame.
WORK = os.path.join(CASE, "zoom_work.ini")

out = os.path.join(CASE, "zoom")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)

for amount in (0.6, 0.7, 0.8, 0.9):
    open(WORK, "w").write("ZOOM\n-1 %.2f\n" % amount)
    tag = "a%02d" % round(amount * 100)
    body = "RENDERDIR\n zoom\nUNLOADALL\nLOADINIFILE\n wick3c.ini\n"
    body += "LOADFILE\n wick3c_1_3.s3d\nSETVIEWPOINT\n iso_b\n"
    body += "LOADINIFILE\n zoom_work.ini\nSETTIMEVAL\n %d.0\nRENDERONCE\n z_%s\n" % (T, tag)
    open(os.path.join(CASE, "wick3c.ssf"), "w").write(body)
    rc = subprocess.run([SMV, "-runscript", "wick3c"], cwd=CASE,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL, timeout=2400).returncode
    print("zoom -1 %.2f  exit %s" % (amount, rc))

print("frames in", out)
