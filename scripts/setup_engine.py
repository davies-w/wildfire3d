"""Fetch the sources, install Homebrew prerequisites, and build the FDS engine.

From a bare machine, one command:

    python3 scripts/setup_engine.py --deps --build

What that does, in order, skipping anything already satisfied:

  1. Xcode Command Line Tools -- git, make and curl come from here.
  2. Homebrew, installed from the official script if `brew` is not on PATH.
  3. `brew bundle` against the repository Brewfile: gcc, open-mpi, cmake.
  4. The FDS source at the release tag, into FDS/src.
  5. HYPRE and SUNDIALS, at the tags Build/makefile asks for, into FDS/src.
  6. Those two libraries, built by the FDS third-party script.
  7. The FDS engine, with HYPRE_HOME and SUNDIALS_HOME exported.
  8. A check that the binary is arm64 and actually contains HYPRE.

Each step fails loudly.  A silent no-op here once produced a binary that built
cleanly and then could not run half the experiments.

    --root DIR    build into DIR instead of FDS/  (for a from-scratch test)
    --jobs N      parallel make jobs, default 4
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BREWFILE = os.path.join(REPO, "Brewfile")

TAG = "FDS-6.11.1"
REPO_URL = "https://github.com/firemodels/fds.git"
HYPRE_URL = "https://github.com/hypre-space/hypre.git"
SUNDIALS_URL = "https://github.com/LLNL/sundials.git"
DIST_URL = ("https://github.com/firemodels/fds/releases/download/%s/"
            "FDS-6.11.1_SMV-6.11.2_osx.sh" % TAG)
BREW_INSTALL = ("https://raw.githubusercontent.com/Homebrew/install/HEAD/"
                "install.sh")
HYPRE_REPO = "hypre-space/hypre"
SUNDIALS_REPO = "LLNL/sundials"


def run(cmd, cwd=None, check=True, env=None, log=None):
    """Run a command, printing it first, and fail loudly unless told not to."""
    print("$ %s%s" % (" ".join(cmd), "   (in %s)" % cwd if cwd else ""),
          flush=True)
    fh = open(log, "w") if log else None
    p = subprocess.run(cmd, cwd=cwd, env=env, check=False, text=True,
                       stdout=fh or None, stderr=fh or None)
    if fh:
        fh.close()
    if check and p.returncode != 0:
        if log:
            print(open(log).read()[-1500:])
        sys.exit("FAILED (exit %d): %s" % (p.returncode, " ".join(cmd)))
    return p


def ensure_clt():
    """git, make and curl all come from the Xcode Command Line Tools."""
    if subprocess.run(["xcode-select", "-p"],
                      capture_output=True).returncode == 0:
        print("command line tools: present")
        return
    print("command line tools: MISSING")
    run(["xcode-select", "--install"], check=False)
    sys.exit("macOS has opened a dialog to install the Command Line Tools, "
             "because there is no non-interactive way to do it. Run this "
             "script again once that has finished.")


def find_brew():
    for p in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
        if os.path.exists(p):
            return p
    from shutil import which
    return which("brew")


def ensure_brew():
    """Install Homebrew if there is none.  Its installer may need a password."""
    brew = find_brew()
    if brew:
        print("homebrew: %s" % brew)
        return brew
    print("homebrew: MISSING -- installing from %s" % BREW_INSTALL)
    run(["bash", "-c", "curl -fsSL %s | bash" % BREW_INSTALL],
        env=dict(os.environ, NONINTERACTIVE="1"))
    brew = find_brew()
    if not brew:
        sys.exit("Homebrew is still not on PATH. If its installer stopped to "
                 "ask for your password, run it once by hand and then run "
                 "this script again.")
    return brew


def brew_bundle(brew):
    """Install the prerequisites declared in the repository Brewfile."""
    c = run([brew, "bundle", "check", "--file", BREWFILE], check=False)
    if c.returncode == 0:
        print("brew bundle: satisfied")
        return
    run([brew, "bundle", "install", "--file", BREWFILE])


def dep_tags(src):
    """The HYPRE and SUNDIALS tags the FDS makefile expects.

    Read from the checkout rather than written here, so they cannot drift from
    what the build actually looks for.
    """
    mk = open(os.path.join(src, "fds", "Build", "makefile")).read()
    found = {}
    for line in mk.split("\n"):
        for name in ("HYPRE_VERSION", "SUNDIALS_VERSION"):
            if line.startswith(name + "="):
                found[name] = line.split("=", 1)[1].strip()
    if len(found) != 2:
        sys.exit("could not read HYPRE_VERSION and SUNDIALS_VERSION out of "
                 "fds/Build/makefile")
    return found["HYPRE_VERSION"], found["SUNDIALS_VERSION"]


def clone_source(src, tag):
    """The engine source belongs at src/fds.

    src/ is the FIREMODELS root: the FDS build scripts look for src/fds/Build
    and install the third-party libraries beside it, in src/libs.  The clone
    is the repository's own top level, so it sits one level down.
    """
    dst = os.path.join(src, "fds")
    if os.path.isdir(os.path.join(dst, ".git")):
        print("fds source: present")
        return dst
    os.makedirs(src, exist_ok=True)
    run(["git", "clone", "--depth", "1", "--branch", tag, REPO_URL, dst])
    return dst


def clone_dep(src, name, url, tag):
    """Clone a third-party source at the tag the FDS build asks for."""
    dst = os.path.join(src, name)
    if os.path.isdir(os.path.join(dst, ".git")):
        have = subprocess.run(["git", "describe", "--tags", "--exact-match"],
                              cwd=dst, capture_output=True,
                              text=True).stdout.strip()
        if have == tag:
            print("%s: present at %s" % (name, tag))
            return dst
        print("%s: present at %s, switching to %s" % (name, have, tag))
        run(["git", "fetch", "--tags", "origin", tag], cwd=dst, check=False)
        run(["git", "checkout", tag], cwd=dst)
        return dst
    run(["git", "clone", url, dst])
    run(["git", "checkout", tag], cwd=dst)
    return dst


def dep_homes(src, hypre_tag, sundials_tag):
    """Where the FDS makefile expects to find the two libraries."""
    return {"HYPRE_HOME": os.path.join(src, "libs", "hypre", hypre_tag),
            "SUNDIALS_HOME": os.path.join(src, "libs", "sundials",
                                          sundials_tag)}


def build_env(src, build_target, homes):
    env = dict(os.environ)
    env.update({"FIREMODELS": src, "FDS_BUILD_TARGET": build_target,
                "COMP_FC": "mpifort", "COMP_CC": "mpicc"})
    env.update(homes)
    env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")
    return env


def build_thirdparty(src, build_target, homes):
    """Build HYPRE and SUNDIALS, and fail if they do not appear.

    This is the step that silently did nothing before: the script checks for a
    source repository, prints nothing when it is absent, and exits zero. The
    build then links no HYPRE at all and reports success.
    """
    build = os.path.join(src, "fds", "Build", build_target)
    log = os.path.join(src, "thirdparty_build.log")
    run(["bash", "-c", "source ../Scripts/build_thirdparty_libs.sh"], cwd=build,
        env=build_env(src, build_target, homes), log=log)
    missing = [h for h in homes.values() if not os.path.isdir(h)]
    if missing:
        sys.exit("the third-party build produced no library at:\n  %s\n"
                 "The engine would build and then fail at runtime on every "
                 "case that needs UGLMAT. Full output in %s"
                 % ("\n  ".join(missing), log))
    for k, v in homes.items():
        print("%s = %s" % (k, v))


def has_hypre(binary):
    """A binary built with -DWITH_HYPRE carries far more hypre symbols."""
    out = subprocess.run(["strings", binary], capture_output=True,
                         text=True).stdout
    return out.lower().count("hypre") > 50


def build_fds(src, build_target, homes, jobs):
    """Build the engine with the two libraries switched on.

    Objects compiled without them have to go, or make keeps them and the
    defines never take effect.  The same applies to an existing binary: the
    make loop below runs only while it is missing.
    """
    build = os.path.join(src, "fds", "Build", build_target)
    binary = os.path.join(build, "fds_" + build_target)
    log = os.path.join(src, "fds_build.log")
    if os.path.exists(binary) and has_hypre(binary):
        print("fds: already built with HYPRE, nothing to do")
        return binary
    if os.path.exists(binary):
        print("fds: existing binary has no HYPRE, rebuilding")
    removed = 0
    for f in os.listdir(build):
        if f.endswith((".o", ".mod")):
            os.remove(os.path.join(build, f))
            removed += 1
    if removed:
        print("removed %d objects compiled without HYPRE" % removed)
    if os.path.exists(binary):
        os.remove(binary)
    for _ in range(8):
        run(["make", "-j%d" % jobs, "VPATH=../../Source", "-f", "../makefile",
             build_target], cwd=build, env=build_env(src, build_target, homes),
            check=False, log=log)
        if os.path.exists(binary):
            break
    if not os.path.exists(binary):
        print(open(log).read()[-2000:])
        sys.exit("the engine did not build; full output in %s" % log)
    return binary


def verify(binary):
    """arm64, and actually carrying HYPRE."""
    t = subprocess.run(["file", binary], capture_output=True, text=True).stdout
    print(t.strip())
    if "arm64" not in t:
        sys.exit("the built binary is not arm64: %s" % t.strip())
    if not has_hypre(binary):
        sys.exit("the built binary carries no HYPRE symbols, so every case "
                 "that needs UGLMAT would fail at runtime")
    print("verified: arm64, with HYPRE")


def dist(root):
    """The NIST binary distribution, which is where Smokeview comes from."""
    install = os.path.join(root, "install")
    os.makedirs(install, exist_ok=True)
    sh = os.path.join(install, "install.sh")
    if not os.path.exists(sh):
        run(["curl", "-fL", "-o", sh, DIST_URL])
    # The installer is interactive and blocks without a TTY, so feed it a
    # choice.  Use bash: macOS sh is bash in POSIX mode and breaks its bashisms.
    run(["bash", "-c", "printf '2\\n' | bash '%s'" % sh], cwd=install)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deps", action="store_true",
                    help="ensure the Command Line Tools, Homebrew, Brewfile")
    ap.add_argument("--dist", action="store_true",
                    help="also fetch the NIST binaries")
    ap.add_argument("--build", action="store_true",
                    help="also build the native arm64 engine")
    ap.add_argument("--root", default=None, help="engine root, default FDS/")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()

    root = os.path.abspath(a.root or os.path.join(REPO, "FDS"))
    src = os.path.join(root, "src")
    target = "ompi_gnu_osx"
    print("engine root: %s" % root)

    if a.deps:
        ensure_clt()
        brew_bundle(ensure_brew())
    clone_source(src, TAG)
    if a.dist:
        dist(root)
    if a.build:
        hypre_tag, sundials_tag = dep_tags(src)
        print("tags from makefile: HYPRE %s, SUNDIALS %s"
              % (hypre_tag, sundials_tag))
        clone_dep(src, "hypre", HYPRE_URL, hypre_tag)
        clone_dep(src, "sundials", SUNDIALS_URL, sundials_tag)
        homes = dep_homes(src, hypre_tag, sundials_tag)
        build_thirdparty(src, target, homes)
        verify(build_fds(src, target, homes, a.jobs))
    print("\nengine root: %s" % root)


if __name__ == "__main__":
    main()
