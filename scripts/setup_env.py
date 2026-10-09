"""Create the project virtualenv and install the pinned analysis dependencies.

The scripts need numpy, pillow and dvc. Those are project dependencies, not
part of the FDS engine, so they belong in a venv at the repo root -- the
engine tree is gitignored and a fresh clone cannot inherit a venv from it.

    python3 scripts/setup_env.py
    .venv/bin/python experiments/07_wick3_house_ignition/read_canopy.py
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = os.path.join(ROOT, ".venv")
PY = os.path.join(VENV, "bin", "python")

if not os.path.exists(PY):
    print("creating %s" % VENV)
    subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
else:
    print("%s already exists" % VENV)

subprocess.run([PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
               check=True)
subprocess.run([PY, "-m", "pip", "install", "--quiet", "-r",
                os.path.join(ROOT, "requirements.txt")], check=True)

print("\ninterpreter: %s" % PY)
print(subprocess.run([PY, "-c", "import numpy, PIL; print('numpy', numpy.__version__)"],
                     capture_output=True, text=True).stdout.strip())
