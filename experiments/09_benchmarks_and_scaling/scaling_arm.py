"""Compare native arm64 FDS with the x86 Rosetta binary, and test OpenMP scaling.

Both binaries run the identical T_END=10 benchmark (153,600 cells) on a fresh
copy of the case, so no run can resume from a previous one.  Rosetta is
measured at 1 thread as the reference point; the native build is swept across
thread counts to see whether parallel scaling recovers without translation.
"""
import os, re, shutil, subprocess, time

SRC = os.path.expanduser("~/FDS/cases/wick2_bench")
BIN = os.path.expanduser("~/FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx")
ROSETTA = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")
RUNS = [("rosetta-x86", ROSETTA, 1), ("arm64", BIN, 1), ("arm64", BIN, 2),
        ("arm64", BIN, 4), ("arm64", BIN, 8)]

base = {}
for tag, binary, nt in RUNS:
    d = os.path.expanduser("~/FDS/cases/scl_%s_%d" % (tag, nt))
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for f in os.listdir(SRC):
        if f.startswith("bench.fds") or f.startswith("bench.ini"):
            shutil.copy(os.path.join(SRC, f), d)
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = str(nt)
    env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")
    t0 = time.time()
    p = subprocess.run([binary, "bench.fds"], cwd=d, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=2400)
    el = time.time() - t0
    base.setdefault(tag, el)
    print("%-12s threads %d  wall %7.1f s  speedup %.2fx  efficiency %3.0f%%"
          % (tag, nt, el, base[tag] / el, 100.0 * (base[tag] / el) / nt), flush=True)

print("native vs rosetta at 1 thread: %.2fx"
      % (base["rosetta-x86"] / base["arm64"]))
