"""Run the clean T_END=350 wick3c solve with the native arm64 FDS at 4 threads.

4 threads is the measured optimum for this mesh size (1.40x); 8 threads was
slightly worse.  CHID stays 'wick3c', RESTART is not used, so every output file
has one unambiguous time axis -- the problem that made the earlier restart data
untrustworthy.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, BIN, NATIVE_FDS  # noqa: E402

import os, re, subprocess, time

CASE = os.path.join(FDS_ROOT, "cases/wick3")
BIN = NATIVE_FDS

# clear any partial output from the aborted x86 attempt
for f in os.listdir(CASE):
    if f.startswith("wick3c_"):
        os.remove(os.path.join(CASE, f))
        print("removed", f)

env = dict(os.environ)
env["OMP_NUM_THREADS"] = "4"
env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")

log = open(os.path.join(CASE, "wick3c_arm.log"), "w")
t0 = time.time()
p = subprocess.Popen([BIN, "wick3c.fds"], cwd=CASE, stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env)
print("launched PID", p.pid, "at", time.strftime("%H:%M:%S"), flush=True)
while p.poll() is None:
    time.sleep(60)
    if time.time() - t0 > 9000:
        p.kill()
        print("TIMEOUT")
        break
log.close()
el = int(time.time() - t0)
print("exit %s after %.1f min" % (p.returncode, el / 60.0))
for l in open(os.path.join(CASE, "wick3c_arm.log")).read().strip().split("\n")[-4:]:
    print("  ", l)
