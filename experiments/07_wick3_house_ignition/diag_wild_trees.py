"""Render iso frames with CANOPY and TRUNK forced to grey.

The .smv is left holding whatever colours the last animation pass wrote, so
every frame of a re-render shows those colours regardless of time.  That makes
it impossible to tell a burning tree (real flame drawn over it) from a tree
that merely shares a surface name with one.

Forcing the two shared surfaces to a flat grey removes the confusion: orange on
a tree is then the flame volume, nothing else.  The .smv is restored at the end.
"""
import os, re, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
sys.path.insert(0, os.path.join(_d, "scripts"))
from paths import FDS_ROOT  # noqa: E402
import case_config  # noqa: E402

CFG = sys.argv[1]
TIMES = sys.argv[2:]
cfg = case_config.load(CFG)
smv = os.path.join(cfg["case_dir"], cfg["chid"] + ".smv")
orig = open(smv).read()
lines = orig.split("\n")
for name in ("CANOPY", "TRUNK"):
    i = next(k for k, l in enumerate(lines) if l.strip() == name)
    f = lines[i + 2].split()
    f[4], f[5], f[6] = "0.55000", "0.55000", "0.55000"
    lines[i + 2] = "  " + "      ".join(f)
open(smv, "w").write("\n".join(lines))
try:
    for t in TIMES:
        out = "/tmp/topview/iso%s_grey.png" % t
        subprocess.run([sys.executable, os.path.join(_d, "scripts/render_view.py"),
                        CFG, t, "iso_b", out], timeout=2400)
        print(out)
finally:
    open(smv, "w").write(orig)
    print("restored .smv")
