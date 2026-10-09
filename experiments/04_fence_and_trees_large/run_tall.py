#!/usr/bin/env python3
"""Run the taller garden case and wait for it, with a hard bound.

Kept in a script so the shell command stays trivial and cannot break.
"""
import os
import subprocess
import time

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
FDS = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds")

log = open(os.path.join(CASE, "run.log"), "w")
proc = subprocess.Popen([FDS, "garden_tall.fds"], cwd=CASE,
                        stdout=log, stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL)
print(f"launched PID {proc.pid}")

t0 = time.time()
while proc.poll() is None:
    time.sleep(20)
    el = int(time.time() - t0)
    if el > 2400:
        proc.kill()
        print("TIMEOUT after 40 min")
        break

log.close()
print(f"exit code {proc.returncode} after {int(time.time() - t0)} s")
tail = open(os.path.join(CASE, "run.log")).read().split("\n")[-6:]
for line in tail:
    if line.strip():
        print("   ", line)
