"""Benchmark the MPI build vs the OpenMP build on the same case.

No case changes -- same mesh, same geometry.  Only the executable and
OMP_NUM_THREADS differ.  T_END cut to 10 s so the benchmark is quick.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os
import re
import subprocess
import time

CASE = os.path.join(FDS_ROOT, "cases/wick2")
BENCH = os.path.join(FDS_ROOT, "cases/wick2_bench")
BIN = os.path.join(FDS_ROOT, "FDS-6.11.1_SMV-6.11.2_osx/bin")

os.makedirs(BENCH, exist_ok=True)
s = open(os.path.join(CASE, "wick2.fds")).read()
s = s.replace("CHID='wick2'", "CHID='bench'").replace("T_END=120.", "T_END=10.")
open(os.path.join(BENCH, "bench.fds"), "w").write(s)


def sim_time(log):
    hits = re.findall(r"Simulation Time:\s+([\d.]+)", log)
    return float(hits[-1]) if hits else 0.0


def run(label, exe, env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    t0 = time.time()
    with open(os.path.join(BENCH, "bench.log"), "w") as lg:
        subprocess.run([os.path.join(BIN, exe), "bench.fds"], cwd=BENCH,
                       stdout=lg, stderr=subprocess.STDOUT,
                       stdin=subprocess.DEVNULL, env=env, timeout=3600)
    wall = time.time() - t0
    sim = sim_time(open(os.path.join(BENCH, "bench.log")).read())
    print(f"  {label:32s} wall {wall:7.1f}s  sim {sim:5.1f}s  "
          f"speed {sim/wall:.3f}")
    return wall


print("benchmark, T_END=10 s, 153,600 cells")
run("fds (MPI build, 1 proc)", "fds", {})
run("fds_openmp OMP_NUM_THREADS=8", "fds_openmp", {"OMP_NUM_THREADS": "8"})
