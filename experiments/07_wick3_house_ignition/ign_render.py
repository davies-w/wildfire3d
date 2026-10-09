"""Render the two passes for the ignition-state animation of wick3c.

Pass A ("norm")  flame volume + firebrands, NO boundary file
                 -> every object in its normal colour
Pass B ("burn")  the SAME flame volume and firebrands, PLUS the BURNING RATE
                 boundary file -> the only difference from pass A is the
                 boundary colouring, so a pixel difference means ignition
                 rather than a change of framing or loaded content

No smoke is loaded in either pass: the point is to read ignition state off the
objects, and smoke obscures them.  One smokeview process renders all frames of
each pass.
"""
import os, shutil, subprocess

CASE = os.path.expanduser("~/FDS/cases/wick3")
SMV = os.path.expanduser("~/FDS/bin/smv_quiet")
TIMES = [40, 90, 140, 180, 200, 220, 240, 260, 280, 300, 320, 350]


def render(sub, files, prefix):
    out = os.path.join(CASE, sub)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    body = "UNLOADALL\nLOADINIFILE\n wick3c.ini\n"
    for f in files:
        body += "LOADFILE\n %s\n" % f
    body += "SETVIEWPOINT\n iso_b\n"
    for t in TIMES:
        body += "SETTIMEVAL\n %d.0\nRENDERONCE\n %s_%03d\n" % (t, prefix, t)
    open(os.path.join(CASE, "wick3c.ssf"), "w").write("RENDERDIR\n %s\n" % sub + body)
    p = subprocess.run([SMV, "-runscript", "wick3c"], cwd=CASE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=2400)
    print("  %-6s exit %s  %d/%d frames"
          % (sub, p.returncode, len(os.listdir(out)), len(TIMES)))


print("rendering (2 smokeview launches total):")
render("norm", ["wick3c_1_3.s3d", "wick3c_1.prt5"], "n")
render("burn", ["wick3c_1_3.s3d", "wick3c_1.prt5", "wick3c_1_2.bf"], "b")
