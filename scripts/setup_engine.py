"""Check out and build the FDS engine under FDS/.

The engine is deliberately not vendored -- it is a large third-party tree plus
build output -- so this script puts it in a known place reproducibly instead of
leaving a copy wherever it happened to land.

    python3 scripts/setup_engine.py                 # source checkout only
    python3 scripts/setup_engine.py --dist          # also the NIST binaries
    python3 scripts/setup_engine.py --build         # also build native arm64

The native arm64 build is worth 1.60x over the x86-64 distribution under
Rosetta (docs/performance.md). Both paths are created under FDS/, which is
gitignored apart from its README.
"""
import argparse, os, subprocess, sys

TAG = "FDS-6.11.1"
REPO_URL = "https://github.com/firemodels/fds.git"
DIST_URL = ("https://github.com/firemodels/fds/releases/download/%s/"
            "FDS-6.11.1_SMV-6.11.2_osx.sh" % TAG)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "FDS")
SRC = os.path.join(ROOT, "src")
INSTALL = os.path.join(ROOT, "install")


def run(cmd, cwd=None, check=True):
    print("$ %s" % " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check)


def clone():
    if os.path.isdir(os.path.join(SRC, ".git")):
        print("source already present at %s" % SRC)
        return
    os.makedirs(os.path.dirname(SRC), exist_ok=True)
    run(["git", "clone", "--depth", "1", "--branch", TAG, REPO_URL, SRC])


def dist():
    os.makedirs(INSTALL, exist_ok=True)
    sh = os.path.join(INSTALL, "install.sh")
    if not os.path.exists(sh):
        run(["curl", "-fL", "-o", sh, DIST_URL])
    # the installer is interactive and blocks without a TTY; feed it a choice.
    # use bash, not sh -- macOS sh is bash in POSIX mode and breaks its bash-isms.
    run(["bash", "-c", "printf '2\\n' | bash '%s'" % sh], cwd=INSTALL)


def build():
    # stage 1 builds third-party libs, stage 2 needs several make passes.
    # HYPRE and SUNDIALS are typically absent; the build is sound without them
    # (experiments/10_build_validation).
    run(["bash", "build_thirdparty_libs.sh"], cwd=os.path.join(SRC, "Build"))
    out = None
    for _ in range(6):
        p = run(["make"], cwd=os.path.join(SRC, "Build"), check=False)
        out = p.returncode
        if out == 0:
            break
    if out != 0:
        sys.exit("build did not complete; see the last make output")
    print("built -- binary under %s/Build/" % SRC)


ap = argparse.ArgumentParser()
ap.add_argument("--dist", action="store_true", help="also fetch the NIST binaries")
ap.add_argument("--build", action="store_true", help="also build native arm64")
a = ap.parse_args()

clone()
if a.dist:
    dist()
if a.build:
    build()
print("\nengine root: %s" % os.path.abspath(ROOT))
