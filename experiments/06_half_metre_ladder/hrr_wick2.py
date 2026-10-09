import csv
import os

p = os.path.expanduser("~/FDS/cases/wick2/wick2_hrr.csv")
rows = list(csv.reader(open(p)))
i = rows[1].index("HRR")
v = [(float(r[0]), float(r[i])) for r in rows[2:] if r and r[i].strip()]
print(f"{'t':>7} {'HRR MW':>10}")
for t, h in v[::max(1, len(v) // 13)]:
    print(f"{t:7.1f} {h/1000:10.2f}")
print(f"peak {max(x for _, x in v)/1000:.1f} MW   final {v[-1][1]/1000:.2f} MW")
