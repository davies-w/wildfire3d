"""Measure FDS OpenMP scaling on the 153,600-cell benchmark mesh.

Runs the same T_END=10 case at several thread counts and reports wall time and
parallel speedup relative to 1 thread.  This decides cloud instance shape:
if the mesh will not use many cores, only clock speed matters.
"""
import os, re, shutil, subprocess, time

CASE = os.path.expanduser("~/FDS/cases/wick2_bench")
FDS = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")
THREADS = [1, 2, 4, 8]

base = None
for nt in THREADS:
    # clear old output so the run cannot resume
    for f in os.listdir(CASE):
        if re.match(r"bench_1_\d+\.(bf|s3d|q|smv|prt5|restart)$", f):
            os.remove(os.path.join(CASE, f))
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = str(nt)
    t0 = time.time()
    subprocess.run([FDS, "bench.fds"], cwd=CASE, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=1800)
    el = time.time() - t0
    if base is None:
        base = el
    print("threads %d  wall %7.1f s  speedup %.2fx  efficiency %.0f%%"
          % (nt, el, base / el, 100.0 * (base / el) / nt))
