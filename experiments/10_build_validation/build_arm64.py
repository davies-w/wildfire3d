"""Build FDS natively for arm64 (OpenMPI + GNU Fortran) on Apple Silicon.

Two stages:
  1. build_thirdparty_libs.sh -- downloads and compiles HYPRE v3.0.0 and
     SUNDIALS v7.5.0, which the FDS makefile requires as link targets.
  2. make, invoked repeatedly -- FDS's makefile compiles the source in batches,
     so one call does not finish the build.

Everything is logged with a hard time limit.
"""
import os, subprocess, time

FIREMODELS = os.path.expanduser("~/FDS/src")
BUILD = os.path.join(FIREMODELS, "fds", "Build", "ompi_gnu_osx")
TARGET = "ompi_gnu_osx"
BIN = os.path.join(BUILD, "fds_" + TARGET)
LOG = os.path.expanduser("~/FDS/arm64_build.log")

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
