"""Run the clean wick3c solve and wait."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, subprocess, time

CASE = os.path.join(FDS_ROOT, "cases/wick3")
FDS = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")

env = dict(os.environ)
env["OMP_NUM_THREADS"] = "8"
log = open(os.path.join(CASE, "wick3c.log"), "w")
p = subprocess.Popen([FDS, "wick3c.fds"], cwd=CASE, stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     env=env)
print("launched PID", p.pid)
t0 = time.time()
while p.poll() is None:
    time.sleep(30)
    if time.time() - t0 > 7200:
        p.kill()
        print("TIMEOUT")
        break
log.close()
el = int(time.time() - t0)
print("exit %s after %d s (%.1f min)" % (p.returncode, el, el / 60.0))
for l in open(os.path.join(CASE, "wick3c.log")).read().strip().split("\n")[-3:]:
    print("  ", l)
