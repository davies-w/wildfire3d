"""Build FDS natively for arm64 (OpenMPI + GNU Fortran) on Apple Silicon.

Two stages:
  1. build_thirdparty_libs.sh -- downloads and compiles HYPRE v3.0.0 and
     SUNDIALS v7.5.0, which the FDS makefile requires as link targets.
  2. make, invoked repeatedly -- FDS's makefile compiles the source in batches,
     so one call does not finish the build.

Everything is logged with a hard time limit.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, BIN, NATIVE_BUILD, BUILD_TAG, NATIVE_FDS  # noqa: E402

import os, subprocess, time

FIREMODELS = os.path.join(FDS_ROOT, "src")
BUILD = NATIVE_BUILD
TARGET = BUILD_TAG
BIN = NATIVE_FDS
LOG = os.path.join(FDS_ROOT, "arm64_build.log")

env = dict(os.environ)
env["FIREMODELS"] = FIREMODELS
env["FDS_BUILD_TARGET"] = TARGET
env["COMP_FC"] = "mpifort"
env["COMP_CC"] = "mpicc"
env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")

t0 = time.time()
log = open(LOG, "w")


def left():
    return 5400 - (time.time() - t0)


print("stage 1: third-party libraries", flush=True)
subprocess.run(["bash", "-c", "source ../Scripts/build_thirdparty_libs.sh"],
               cwd=BUILD, env=env, stdout=log, stderr=subprocess.STDOUT,
               stdin=subprocess.DEVNULL, timeout=max(60, left()))
print("stage 1 done at %.1f min" % ((time.time() - t0) / 60.0), flush=True)

# Build scripts unsets these on exit, and Build/makefile only compiles the HYPRE
# and SUNDIALS code ifdef on them (makefile:112,119).  Stage 2 runs in a
# different process with this environment, so they must be set here or FDS is
# built without either library.  That is exactly what happened: no HYPRE, so no
# -DWITH_HYPRE, and every case where FDS picks the UGLMAT pressure solver died
# at startup with 'HYPRE selected for UGLMAT solver without compiling and
# linking HYPRE library'.
HYPRE_HOME = os.path.join(FIREMODELS, "libs/hypre/v3.0.0")
SUNDIALS_HOME = os.path.join(FIREMODELS, "libs/sundials/v7.5.0")
for label, home in (("HYPRE_HOME", HYPRE_HOME), ("SUNDIALS_HOME", SUNDIALS_HOME)):
    print("%-14s = %s  exists=%s" % (label, home, os.path.isdir(home)))
env["HYPRE_HOME"] = HYPRE_HOME
env["SUNDIALS_HOME"] = SUNDIALS_HOME

# Objects compiled without those defines must go, or make keeps them and the
# flags never take effect.
removed = 0
for f in os.listdir(BUILD):
    if f.endswith(".o") or f.endswith(".mod"):
        os.remove(os.path.join(BUILD, f))
        removed += 1
print("removed %d stale objects" % removed, flush=True)

# Stage 2 runs make only while the binary is missing, so an existing binary has
# to go or a rebuild with new flags would never happen.
if os.path.exists(BIN):
    os.remove(BIN)
    print("removed previous binary %s" % BIN, flush=True)

print("stage 2: fds", flush=True)
attempt = 0
while not os.path.exists(BIN) and left() > 0:
    attempt += 1
    subprocess.run(["make", "-j4", "VPATH=../../Source", "-f", "../makefile", TARGET],
                   cwd=BUILD, env=env, stdout=log, stderr=subprocess.STDOUT,
                   stdin=subprocess.DEVNULL)
log.close()

el = int(time.time() - t0)
print("finished in %.1f min after %d make passes" % (el / 60.0, attempt))
print("binary exists:", os.path.exists(BIN))
if os.path.exists(BIN):
    print(subprocess.run(["file", BIN], capture_output=True, text=True).stdout.strip())
else:
    for l in open(LOG).read().strip().split("\n")[-30:]:
        print("  ", l)
