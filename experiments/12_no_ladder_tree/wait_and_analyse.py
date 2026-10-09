"""Wait for the wick4 solve, then extract the house wall temperature history.

Waits in-process with a hard timeout rather than sleeping in the shell.

Patch 2 is the house west face (x = 18, y 8..16, z 0..3.5) -- the surface the
fence spur attaches to, and the same face measured in experiment 07, so the two
cases are directly comparable.

    python3 wait_and_analyse.py
"""
import os, subprocess, sys, time

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import DIST, FDS_ROOT  # noqa: E402

CASE = os.path.join(FDS_ROOT, "cases/wick4")
F2A = os.path.join(DIST, "bin/fds2ascii")
WINDOWS = [48, 100, 148, 200, 248, 300]
IGN = 350.0
LIMIT = 7200


def solving():
    r = subprocess.run(["pgrep", "-f", "fds_ompi_gnu_osx wick4.fds"],
                       capture_output=True, text=True)
    return r.returncode == 0


def wall_temp(t0):
    out = "wt_%03d.txt" % t0
    stdin = "wick4\n3\n1\nn\n%d %d\n-1\n1\n1\n%s\n" % (t0, t0 + 2, out)
    subprocess.run([F2A], cwd=CASE, input=stdin, text=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=1800)
    path = os.path.join(CASE, out)
    if not os.path.exists(path):
        return None
    vals, seen = [], False
    for line in open(path):
        if line.startswith("Patch"):
            if seen:
                break
            seen = "18.00<x<  18.00" in line and "8.00<y<  16.00" in line
            continue
        if seen:
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    vals.append(float(parts[3]))
                except ValueError:
                    pass
    return vals


if __name__ == "__main__":
    t0 = time.time()
    while solving():
        if time.time() - t0 > LIMIT:
            sys.exit("still solving after %d s" % LIMIT)
        time.sleep(60)
    print("solver finished after %.0f min\n" % ((time.time() - t0) / 60))

    print("%6s %10s %10s %12s" % ("t (s)", "mean C", "max C", "cells>350C"))
    for w in WINDOWS:
        v = wall_temp(w)
        if not v:
            print("%6d   no data" % w)
            continue
        hot = sum(1 for x in v if x > IGN)
        print("%6d %10.1f %10.1f %7d/%d"
              % (w, sum(v) / len(v), max(v), hot, len(v)))
