"""Run wick3 on the OpenMP build with 8 threads, and wait."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import subprocess
import time

CASE = os.path.join(FDS_ROOT, "cases/wick3")
FDS = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")

env = dict(os.environ)
env["OMP_NUM_THREADS"] = "8"
log = open(os.path.join(CASE, "run.log"), "w")
p = subprocess.Popen([FDS, "wick3.fds"], cwd=CASE, stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     env=env)
print("launched PID", p.pid, "OMP_NUM_THREADS=8")
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
for l in open(os.path.join(CASE, "run.log")).read().strip().split("\n")[-3:]:
    print("  ", l)
