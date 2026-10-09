"""Render one frame from a chosen Smokeview viewpoint.

Smokeview defines six default viewpoints by name -- XMIN, XMAX, YMIN, YMAX,
ZMIN, ZMAX -- each looking at the centre of the scene from that direction.
ZMAX is a plan view, which removes the projection ambiguity of the 3/4 iso
view: what you see is directly above what it is.

    python3 render_view.py <render.json> <time> <viewpoint> <out.png>
"""
import os, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402
import case_config  # noqa: E402

if len(sys.argv) < 5:
    sys.exit("usage: render_view.py <render.json> <time> <viewpoint> <out.png>")
cfg = case_config.load(sys.argv[1])
t, view, out = sys.argv[2], sys.argv[3], os.path.abspath(sys.argv[4])
sub = os.path.dirname(out)

body = "RENDERDIR\n %s\nUNLOADALL\nLOADINIFILE\n %s\n" % (
    sub, os.path.basename(cfg["view_ini"]))
for f in cfg["volumes"]:
    body += "LOADFILE\n %s\n" % f
body += "SETVIEWPOINT\n %s\n" % view
body += "SMOKEPROP\n %g\n" % cfg["smokeprop"]
body += "SETTIMEVAL\n %s.0\nRENDERONCE\n %s\n" % (t, os.path.basename(out)[:-4])
open(cfg["ssf"], "w").write(body)

rc = subprocess.run([os.path.join(FDS_ROOT, "bin/smv_quiet"), "-runscript",
                     cfg["chid"]], cwd=cfg["case_dir"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL, timeout=2400).returncode
print("exit %s -> %s" % (rc, out))
