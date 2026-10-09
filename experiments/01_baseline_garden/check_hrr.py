"""Was there any fire in the wick run?  Read the HRR record."""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import csv
import os

p = os.path.join(FDS_ROOT, "cases/garden_tall/wick_hrr.csv")
rows = list(csv.reader(open(p)))
names = rows[1]
i = names.index("HRR")
v = [(float(r[0]), float(r[i])) for r in rows[2:] if r and r[i].strip()]
print("samples:", len(v), " t_max:", v[-1][0])
print(f"{'t':>7} {'HRR kW':>12}")
for t, h in v[::max(1, len(v) // 14)]:
    print(f"{t:7.1f} {h:12.1f}")
print(f"peak HRR {max(x for _, x in v) / 1000:.2f} MW")
