"""Single source of truth for where the engine and its data live.

Rule 1 of AGENTS.md: no script may hardcode a working-area path. Everything
routes through FDS_ROOT, which defaults to the in-repo FDS/ directory and is
overridable with WILDFIRE3D_FDS for a checkout somewhere else.

Scripts find this module by walking up from their own location, so it works
from any depth without sys.path guesswork.
"""
import os

REPO = os.path.dirname(os.path.abspath(__file__))

FDS_ROOT = os.environ.get("WILDFIRE3D_FDS", os.path.join(REPO, "FDS"))

# Convenience anchors -- most scripts want one of these.
CASES = os.path.join(FDS_ROOT, "cases")
RUNS = os.path.join(FDS_ROOT, "runs")
BIN = os.path.join(FDS_ROOT, "bin")

# The NIST binary distribution and the native build, if present.
DIST = os.path.join(FDS_ROOT, "install")
SRC = os.path.join(FDS_ROOT, "src")

# The project virtualenv lives at the repo root, NOT inside the engine tree --
# FDS/ is gitignored, so a venv there could not be reproduced from a clone.
# Create it with scripts/setup_env.py.
VENV = os.path.join(REPO, ".venv")
VENV_BIN = os.path.join(VENV, "bin")
VENV_PY = os.path.join(VENV_BIN, "python")
