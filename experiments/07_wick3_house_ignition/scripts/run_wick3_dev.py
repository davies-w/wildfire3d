"""Run wick3_dev (restart to t=600 with devices) and wait."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import shutil
import subprocess
import time

CASE = os.path.join(FDS_ROOT, "cases/wick3")
BAK = os.path.join(CASE, "pre_restart600")
FDS = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")

os.makedirs(BAK, exist_ok=True)
for f in os.listdir(CASE):
    if f.endswith(".csv") or f.endswith(".restart"):
        shutil.copy(os.path.join(CASE, f), os.path.join(BAK, f))
print("backed up to pre_restart600:", sorted(os.listdir(BAK)))

env = dict(os.environ)
env["OMP_NUM_THREADS"] = "8"
log = open(os.path.join(CASE, "dev.log"), "w")
p = subprocess.Popen([FDS, "wick3_dev.fds"], cwd=CASE, stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     env=env)
print("launched PID", p.pid)
t0 = time.time()
while p.poll() is None:
    time.sleep(30)
    if time.time() - t0 > 5400:
        p.kill()
        print("TIMEOUT")
        break
log.close()
el = int(time.time() - t0)
print(f"exit {p.returncode} after {el} s ({el/60:.1f} min)")
txt = open(os.path.join(CASE, "dev.log")).read()
for l in txt.strip().split("\n")[-4:]:
    print("  ", l)
errs = [l for l in txt.split("\n") if "ERROR" in l]
for e in errs[:4]:
    print("  ERR:", e.strip())
