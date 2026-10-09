"""Solve wick4: experiment 07's case with the ladder tree removed, T_END=300.

Native arm64 build at 4 threads, the measured optimum for a mesh this size.
No restart, so every output file has one unambiguous time axis.

Run to 300 s rather than 350: the wall is fully above its ignition temperature
by t = 300 and only gains ~80 C in the next 50 s, so the extra 50 s costs about
10 minutes and shows nothing new.

Launched detached by `start_wick4.py`, since it takes about an hour.
"""
import os, shutil, subprocess, sys, time

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, NATIVE_FDS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(FDS_ROOT, "cases/wick4")
os.makedirs(CASE, exist_ok=True)
shutil.copy(os.path.join(HERE, "wick4.fds"), CASE)

env = dict(os.environ)
env["OMP_NUM_THREADS"] = "4"

log_path = os.path.join(CASE, "wick4_arm.log")
t0 = time.time()
with open(log_path, "w") as log:
    p = subprocess.Popen([NATIVE_FDS, "wick4.fds"], cwd=CASE, stdout=log,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         env=env)
    print("launched PID %d at %s" % (p.pid, time.strftime("%H:%M:%S")), flush=True)
    while p.poll() is None:
        time.sleep(60)
        if time.time() - t0 > 8000:
            p.kill()
            print("TIMEOUT after %.0f min" % ((time.time() - t0) / 60))
            break
    code = p.returncode

print("exit %s after %.1f min" % (code, (time.time() - t0) / 60.0))
for line in open(log_path).read().strip().split("\n")[-4:]:
    print("  " + line)
