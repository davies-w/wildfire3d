"""Compare the two wtest HRR records: NIST x86 (Rosetta) vs native arm64.

Both runs used identical input, single threaded, T_END=30 s.  The arm64 build
linked without HYPRE and SUNDIALS, so this checks whether those libraries
actually affect our cases.  Agreement to round-off means the build is sound.
"""
import csv, os

def load(p):
    with open(p) as fh:
        rows = list(csv.reader(fh))
    hdr = [h.strip() for h in rows[1]]
    data = [[float(x) for x in r] for r in rows[2:] if r and r[0].strip()]
    return hdr, data

hx, dx = load(os.path.expanduser("~/FDS/cases/valid_x86/wtest_hrr.csv"))
ha, da = load(os.path.expanduser("~/FDS/cases/valid_arm/wtest_hrr.csv"))

print("x86 rows %d  arm rows %d" % (len(dx), len(da)))
print("columns:", [h for h in hx if h])
if len(dx) != len(da):
    print("WARNING: row counts differ")
n = min(len(dx), len(da))

for j, name in enumerate(hx):
    if not name:
        continue
    xs = [dx[i][j] for i in range(n)]
    as_ = [da[i][j] for i in range(n)]
    diffs = [abs(a - b) for a, b in zip(xs, as_)]
    scale = max(max(abs(v) for v in xs), 1e-30)
    print("%-10s max|diff| %11.3e   max|value| %11.4g   rel %9.2e"
          % (name, max(diffs), scale, max(diffs) / scale))
