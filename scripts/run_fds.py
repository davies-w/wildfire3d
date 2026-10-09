"""Solve FDS decks with the native arm64 build, one or more at a time.

    python3 run_fds.py deck.fds [deck.fds ...] [--threads 4] [--jobs 2]
                                [--timeout 8000]

Each deck is copied into FDS/cases/<deck name>/ and solved there, so the copy in
the experiment directory stays the record of exactly what was run.  The deck's
&HEAD CHID must equal its file name: FDS derives output names from the file name
and refuses to start otherwise, which is checked before anything is launched.

Several decks with --jobs > 1 run concurrently, each with its own thread count,
so a paired experiment costs one run's wall clock rather than two.  Four threads
is the measured optimum for this mesh on the 8-CPU M2.
"""
import argparse, os, shutil, subprocess, sys, time

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT, NATIVE_FDS  # noqa: E402


def chid_of(deck):
    """The CHID declared in &HEAD, checked against the file name."""
    for line in open(deck):
        if line.upper().startswith("&HEAD") or line.upper().startswith("&HEAD "):
            for part in line.replace(",", " ").split():
                if part.upper().startswith("CHID="):
                    name = part.split("=", 1)[1].strip().strip("'/")
                    want = os.path.basename(deck)[:-4]
                    if name != want:
                        sys.exit("CHID '%s' in %s does not match the file name "
                                 "'%s'; FDS will refuse to run it."
                                 % (name, deck, want))
                    return name
    sys.exit("no &HEAD CHID found in %s" % deck)


def launch(deck, threads, case_name=None):
    """Copy the deck into its case directory and start FDS there.

    The case directory defaults to the deck's CHID, but not every run uses that
    -- experiment 07 solved `wick3c.fds` into `FDS/cases/wick3`, and its outputs
    are named from the CHID, so the directory has to be nameable.
    """
    name = chid_of(deck)
    case = os.path.join(FDS_ROOT, "cases", case_name or name)
    os.makedirs(case, exist_ok=True)
    shutil.copy(os.path.abspath(deck), case)
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = str(threads)
    log = open(os.path.join(case, name + "_arm.log"), "w")
    p = subprocess.Popen([NATIVE_FDS, name + ".fds"], cwd=case, stdout=log,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         env=env)
    print("launched %-14s pid %-7d %s" % (name, p.pid, time.strftime("%H:%M:%S")),
          flush=True)
    return {"name": name, "case": case, "proc": p, "log": log, "t0": time.time()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--case", dest="case", default=None,
                    help="case directory for a single deck (default: its CHID)")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=8000.0, help="minutes")
    a = ap.parse_args()

    running, done = [], []
    todo = list(a.decks)
    while todo or running:
        while todo and len(running) < a.jobs:
            running.append(launch(todo.pop(0), a.threads, a.case))
        time.sleep(30)
        for job in list(running):
            mins = (time.time() - job["t0"]) / 60.0
            if job["proc"].poll() is None:
                if mins > a.timeout:
                    job["proc"].kill()
                    print("%-14s TIMEOUT after %.0f min" % (job["name"], mins))
                else:
                    continue
            job["log"].close()
            running.remove(job)
            done.append(job)
            print("%-14s exit %-4s after %.1f min"
                  % (job["name"], job["proc"].returncode, mins), flush=True)

    for job in done:
        tail = open(os.path.join(job["case"], job["name"] + "_arm.log"))
        lines = tail.read().strip().split("\n")
        print("\n%s:" % job["name"])
        for line in lines[-3:]:
            print("  " + line)


if __name__ == "__main__":
    main()
