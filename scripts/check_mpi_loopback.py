"""Measure what FDS listens on, to settle whether it can be kept off a network.

FDS is an MPI build, so MPI_Init runs at startup and opens a TCP socket even
when FDS is launched as a single local process.  On this machine that socket
comes up as `*:1024` -- every interface -- so macOS's application firewall asks
for permission and a port is reachable that nothing needs.

Four settings were tried and all four changed nothing, which is why they are
not in scripts/run_fds.py:

  OMPI_MCA_oob_tcp_if_include=lo0      Open MPI 5 has no `oob` framework at all
                                       (`ompi_info --param oob tcp` reports it
                                       as missing), so this name is inert.
  PRTE_MCA_oob_tcp_if_include=lo0       no effect
  PMIX_MCA_ptl_tcp_if_include=lo0       no effect
  PMIX_MCA_ptl_tcp_if_include=127.0.0.1/32   no effect

The reason appears to be structural: PMIx 5 dropped its unix-socket transport
("PMIx no longer supports the \"usock\" transport for client-server" is in the
installed library), leaving TCP as the only client-server transport, and its
interface-include parameter does not take effect here.

So the practical answer is the firewall dialog: choose Deny.  FDS runs as one
process with no MPI peers, so nothing should ever connect to that socket and
the solve does not need it.  That is reasoning from the configuration, not a
measurement -- the measurement this script makes is only the bind address.

    python3 check_mpi_loopback.py <deck.fds> [--seconds 25] [--plain]

--plain runs without any MPI settings, which is the baseline.  Worth re-running
after an Open MPI upgrade: a later version may honour the parameter.
"""
import argparse, os, subprocess, sys, time

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import NATIVE_FDS  # noqa: E402

# The settings tried so far, kept here so a later Open MPI can be re-tested
# against them.  All four measured no effect on this machine.
CANDIDATES = {
    "OMPI_MCA_oob_tcp_if_include": "lo0",
    "PRTE_MCA_oob_tcp_if_include": "lo0",
    "PMIX_MCA_ptl_tcp_if_include": "127.0.0.1/32",
    "OMPI_MCA_btl_tcp_if_include": "lo0",
}

LOOPBACK = ("127.0.0.1", "::1", "[::1]", "localhost")


def listeners(pid):
    """TCP sockets this process is listening on, as lsof sees them."""
    p = subprocess.run(["lsof", "-nP", "-p", str(pid), "-a", "-iTCP",
                        "-sTCP:LISTEN"], capture_output=True, text=True)
    rows = [l.split(None, 8)[-1].strip() for l in p.stdout.split("\n")[1:]
            if l.strip()]
    return rows


def run_once(deck, seconds, plain):
    env = dict(os.environ, OMP_NUM_THREADS="4")
    for k in CANDIDATES:
        env.pop(k, None)
    if not plain:
        env.update(CANDIDATES)
    data = "/tmp/mpi_loopback_check"
    os.makedirs(data, exist_ok=True)
    log = open(os.path.join(data, "run.log"), "w")
    p = subprocess.Popen([NATIVE_FDS, os.path.abspath(deck)], cwd=data,
                         env=env, stdout=log, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL)
    time.sleep(seconds)
    rows = listeners(p.pid) if p.poll() is None else []
    alive = p.poll() is None
    if alive:
        p.kill()
        p.wait()
    return rows, alive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--plain", action="store_true",
                    help="omit the MCA settings, reproducing the problem")
    a = ap.parse_args()

    rows, alive = run_once(a.deck, a.seconds, a.plain)
    label = "without the MCA settings" if a.plain else "with MCA on lo0"
    print("=== %s" % label)
    if not rows:
        print("  no listening sockets seen%s"
              % ("" if alive else " (process had already exited)"))
        return
    outside = []
    for r in rows:
        print("  %s" % r)
        if not any(lo in r for lo in LOOPBACK):
            outside.append(r)
    print("\n  non-loopback listeners: %d" % len(outside))
    if outside:
        print("  -> reachable from outside; the firewall will ask")
    else:
        print("  -> loopback only; nothing outside can reach it")


if __name__ == "__main__":
    main()
