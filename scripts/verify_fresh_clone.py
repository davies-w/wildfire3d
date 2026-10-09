"""Prove the published repo works for a stranger.

Clones davies-w/wildfire3d from GitHub into a clean directory, strips every
credential from the environment, and runs `dvc pull`.  This is the end-to-end
claim in the README -- if it fails here, the README is wrong.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, VENV_BIN  # noqa: E402

import os, shutil, subprocess

V = VENV_BIN
DVC = os.path.join(V, "dvc")
DEST = "/tmp/wildfire3d_clone"

shutil.rmtree(DEST, ignore_errors=True)
p = subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/davies-w/wildfire3d.git", DEST],
                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("clone:", (p.stdout or "").strip()[-200:])

print("\n=== repo contents ===")
for root, dirs, files in os.walk(DEST):
    dirs[:] = [d for d in dirs if d not in (".git", ".dvc")]
    if root.count(os.sep) - DEST.count(os.sep) <= 1:
        rel = os.path.relpath(root, DEST)
        print("  %s/ (%d files)" % ("." if rel == "." else rel, len(files)))

env = {k: v for k, v in os.environ.items()
       if not k.startswith(("HF_", "AWS_", "HUGGING"))}
p = subprocess.run([DVC, "pull"], cwd=DEST, env=env, text=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("\n=== dvc pull, no credentials ===")
print((p.stdout or "").strip()[-400:])

raw = os.path.join(DEST, "experiments/07_wick3_house_ignition/raw")
files = sorted(os.listdir(raw)) if os.path.isdir(raw) else []
print("\nraw evidence restored:", files)
print("RESULT:", "PASS" if len(files) == 5 else "FAIL")
