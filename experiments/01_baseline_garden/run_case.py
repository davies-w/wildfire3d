#!/usr/bin/env python3
"""Run a named FDS case and wait, with a hard bound."""
import os
import subprocess
import sys
import time

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
FDS = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds")
case = sys.argv[1] if len(sys.argv) > 1 else "house_risk"
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2400

log = open(os.path.join(CASE, f"{case}.log"), "w")
p = subprocess.Popen([FDS, f"{case}.fds"], cwd=CASE, stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
print(f"launched {case} PID {p.pid}")
t0 = time.time()
while p.poll() is None:
    time.sleep(20)
    if time.time() - t0 > limit:
        p.kill()
        print("TIMEOUT")
        break
log.close()
print(f"exit {p.returncode} after {int(time.time() - t0)} s")
print(open(os.path.join(CASE, f"{case}.log")).read().strip().split("\n")[-1])
