"""Solve FDS decks with the native arm64 build, writing into a data directory.

    python3 run_fds.py deck.fds:data_dir [deck.fds:data_dir ...]
                        [--threads 4] [--jobs 2] [--timeout 240]

Each deck is solved with its working directory set to that experiment's `data/`
directory, which is where FDS writes everything.  The deck is config and stays
where it is; it is passed as a path argument.  Nothing is copied.

That follows from the source, not from assumption:

- `func.f90:176` -- the input file is the first command line argument, and
  `read.f90:88` inquires on it as given, so a path works.
- `main.f90:3939,4381+` -- output names are built as `CHID` + suffix with no
  directory part, so they land in the working directory.
- `read.f90:435,480` -- CHID comes from `&HEAD`; if omitted it is taken from the
  input filename with the extension stripped.  It is never compared against the
  filename, so a deck may be named anything, but `ERROR(108)` forbids periods
  in CHID.

Several decks run concurrently with `--jobs`, so a paired experiment costs one
run's wall clock rather than two.  Four threads is the measured optimum for
this mesh on the 8-CPU M2; 8 is slower and Rosetta is 2.27x slower.
"""
import argparse, os, subprocess, sys, time

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import NATIVE_FDS  # noqa: E402


def chid_of(deck):
    """CHID from &HEAD, or the deck's root name when &HEAD omits it."""
    for line in open(deck):
        if line.upper().startswith("&HEAD"):
            for part in line.replace(",", " ").split():
                if part.upper().startswith("CHID="):
                    return part.split("=", 1)[1].strip().strip("'/")
    return os.path.basename(deck)[:-4]


def launch(deck, data, threads):
    """Run FDS on a deck, with its working directory in the experiment's data."""
    deck, data = os.path.abspath(deck), os.path.abspath(data)
    os.makedirs(data, exist_ok=True)
    name = chid_of(deck)
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = str(threads)
    log = open(os.path.join(data, name + ".log"), "w")
    p = subprocess.Popen([NATIVE_FDS, deck], cwd=data, stdout=log,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         env=env)
    print("launched %-18s pid %-7d %s" % (name, p.pid, time.strftime("%H:%M:%S")),
          flush=True)
    return {"name": name, "data": data, "proc": p, "log": log, "t0": time.time()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+", metavar="deck.fds:data_dir")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--jobs", dest="parallel", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=240.0, help="minutes")
    a = ap.parse_args()

    pairs = []
    for spec in a.specs:
        if ":" not in spec:
            sys.exit("expected deck.fds:data_dir, got %r" % spec)
        pairs.append(spec.rsplit(":", 1))

    running, done, todo = [], [], list(pairs)
    while todo or running:
        while todo and len(running) < a.parallel:
            deck, data = todo.pop(0)
            running.append(launch(deck, data, a.threads))
        time.sleep(30)
        for job in list(running):
            mins = (time.time() - job["t0"]) / 60.0
            if job["proc"].poll() is None:
                if mins > a.timeout:
                    job["proc"].kill()
                    print("%-18s TIMEOUT after %.0f min" % (job["name"], mins))
                else:
                    continue
            job["log"].close()
            running.remove(job)
            done.append(job)
            print("%-18s exit %-4s after %.1f min"
                  % (job["name"], job["proc"].returncode, mins), flush=True)

    for job in done:
        lines = open(os.path.join(job["data"], job["name"] + ".log")) \
            .read().strip().split("\n")
        print("\n%s:" % job["name"])
        for line in lines[-3:]:
            print("  " + line)

if __name__ == "__main__":
    main()
