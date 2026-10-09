"""Show how the x86-vs-arm64 difference grows over time.

FDS is a chaotic LES, so two builds differing only in floating-point ordering
will agree at early times and then diverge exponentially.  A genuine build
difference (e.g. missing HYPRE/SUNDIALS changing the physics) shows up as a
large difference from the very first recorded step.

Prints time, both HRR values, and the running relative difference.
"""
import csv, os


def load(p):
    with open(p) as fh:
        rows = list(csv.reader(fh))
    return [[float(x) for x in r] for r in rows[2:] if r and r[0].strip()]


dx = load(os.path.expanduser("~/FDS/cases/valid_x86/wtest_hrr.csv"))
da = load(os.path.expanduser("~/FDS/cases/valid_arm/wtest_hrr.csv"))

print("%8s %12s %12s %12s %10s" % ("time", "x86 HRR", "arm HRR", "abs diff", "rel diff"))
n = min(len(dx), len(da))
peak = 0.0
for i in range(n):
    tx, hx = dx[i][0], dx[i][1]
    ta, ha = da[i][0], da[i][1]
    d = abs(hx - ha)
    r = d / max(abs(hx), 1.0)
    peak = max(peak, r)
    if i < 8 or i % 4 == 0 or r > 0.9 * peak:
        print("%8.2f %12.1f %12.1f %12.1f %10.3e" % (tx, hx, ha, d, r))
print("peak relative HRR difference: %.3e" % peak)
