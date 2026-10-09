"""Run wick3 on the OpenMP build with 8 threads, and wait."""
import os
import subprocess
import time

CASE = os.path.expanduser("~/FDS/cases/wick3")
FDS = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")

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
