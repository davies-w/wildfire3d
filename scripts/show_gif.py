"""Point a stable, bookmarkable URL at the newest animation.

Rendering a new gif writes to a per-case path, and hunting for it each time is
tedious.  This keeps ~/FDS/latest.gif symlinked to whichever gif was produced
last, so a single bookmarked file:// URL always shows the current result --
just reload the Safari tab after a re-render.

Usage:  python3 show_gif.py [path/to/some.gif]
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, sys

LATEST = os.path.join(FDS_ROOT, "latest.gif")
CASE_GIF = os.path.join(FDS_ROOT, "cases/wick3/ignition_clean.gif")

src = sys.argv[1] if len(sys.argv) > 1 else CASE_GIF
if not os.path.exists(src):
    sys.exit("no such gif: %s" % src)

if os.path.islink(LATEST) or os.path.exists(LATEST):
    os.remove(LATEST)
os.symlink(os.path.abspath(src), LATEST)

print("latest.gif -> %s" % os.path.basename(os.path.dirname(src)) + "/" + os.path.basename(src))
print()
print("file://" + LATEST)
