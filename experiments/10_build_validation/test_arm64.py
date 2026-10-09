"""Sanity-check the native arm64 FDS binary on a copy of the benchmark case."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, re, shutil, subprocess, time

SRC = os.path.join(FDS_ROOT, "cases/wick2_bench")
DST = os.path.join(FDS_ROOT, "cases/arm_bench")
BIN = os.path.join(FDS_ROOT, "src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx")

shutil.rmtree(DST, ignore_errors=True)
os.makedirs(DST)
for f in os.listdir(SRC):
    if f.startswith("bench.fds") or f.startswith("bench.ini"):
        shutil.copy(os.path.join(SRC, f), DST)

env = dict(os.environ)
env["OMP_NUM_THREADS"] = "1"
env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")
t0 = time.time()
p = subprocess.run([BIN, "bench.fds"], cwd=DST, env=env, capture_output=True,
                   text=True, stdin=subprocess.DEVNULL, timeout=1800)
el = time.time() - t0
print("exit code:", p.returncode, " wall: %.1f s" % el)
tail = (p.stdout or "").strip().split("\n")[-6:]
for l in tail:
    print("  ", l)
out = os.path.join(DST, "bench.out")
if os.path.exists(out):
    txt = open(out).read()
    print("--- .out tail ---")
    for l in txt.strip().split("\n")[-5:]:
        print("  ", l)
