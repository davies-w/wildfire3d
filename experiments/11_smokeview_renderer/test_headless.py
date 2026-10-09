"""Test whether smokeview -runhtmlscript renders PNG images headlessly.

Writes a one-frame script into the wick3 case and runs it both ways, then
reports what each produced.  If -runhtmlscript yields PNGs, rendering can be
done with no window at all.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, shutil, subprocess

CASE = os.path.join(FDS_ROOT, "cases/wick3")
SMV = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")

SCRIPT = ("UNLOADALL\nLOADINIFILE\n wick3.ini\n"
          "LOADFILE\n wick3_1_3.s3d\nLOADFILE\n wick3_1.prt5\n"
          "SETVIEWPOINT\n iso_b\nSETTIMEVAL\n 300.0\n"
          "RENDERONCE\n ht\n")

for tag, args in [("html", ["-runhtmlscript"]), ("normal", ["-runscript"])]:
    d = os.path.join(CASE, "test_" + tag)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    open(os.path.join(CASE, "wick3.ssf"), "w").write(
        "RENDERDIR\n test_%s\n" % tag + SCRIPT)
    p = subprocess.run([SMV] + args + ["wick3"], cwd=CASE,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       stdin=subprocess.DEVNULL, timeout=600, text=True)
    files = sorted(os.listdir(d))
    print("%-7s exit %s  produced %d files: %s"
          % (tag, p.returncode, len(files), files[:6]))
    if p.stdout.strip():
        print("   stdout tail:", p.stdout.strip().split("\n")[-3:])
