"""Run wick2 and wait, with a hard bound."""
import os
import subprocess
import time

CASE = os.path.expanduser("~/FDS/cases/wick2")
FDS = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds")

log = open(os.path.join(CASE, "run.log"), "w")
p = subprocess.Popen([FDS, "wick2.fds"], cwd=CASE, stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
print("launched PID", p.pid)
t0 = time.time()
while p.poll() is None:
    time.sleep(30)
    if time.time() - t0 > 5400:
        p.kill()
        print("TIMEOUT")
        break
log.close()
print(f"exit {p.returncode} after {int(time.time() - t0)} s")
tail = open(os.path.join(CASE, "run.log")).read().strip().split("\n")[-3:]
for l in tail:
    print("  ", l)
