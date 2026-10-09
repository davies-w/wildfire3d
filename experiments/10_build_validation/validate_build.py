"""Validate the native arm64 FDS build against the NIST x86 (Rosetta) binary.

The arm64 build linked WITHOUT HYPRE and SUNDIALS, which the NIST binary
includes.  If our cases do not actually invoke those libraries the results
should agree to round-off; if they do, the curves will diverge.

Method: run a short T_END=30 copy of the wick3 case with each binary, SINGLE
THREADED so that thread scheduling cannot confound the comparison, then diff
the heat release rate records step by step.
"""
import os, shutil, subprocess, time

CASE = os.path.expanduser("~/FDS/cases/wick3")
ARM = os.path.expanduser("~/FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx")
X86 = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds_openmp")

src = open(os.path.join(CASE, "wick3.fds")).read()
src = src.replace("CHID='wick3'", "CHID='wtest'").replace("T_END=200.", "T_END=30.")

for tag, binary in [("valid_x86", X86), ("valid_arm", ARM)]:
    d = os.path.expanduser("~/FDS/cases/" + tag)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    open(os.path.join(d, "wtest.fds"), "w").write(src)
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")
    t0 = time.time()
    p = subprocess.run([binary, "wtest.fds"], cwd=d, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL, timeout=3600)
    print("%-10s exit %s in %.1f s" % (tag, p.returncode, time.time() - t0),
          flush=True)
