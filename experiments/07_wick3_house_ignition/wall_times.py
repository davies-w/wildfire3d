"""Track the house WEST wall temperature through the run.

patch 2 is the x=18 plane, y 8-16, z 0-3.5 -- the house wall facing the fire.
"""
import glob
import re
import os

import numpy as np


def patch_rows(path, want):
    cur, rows = None, []
    for line in open(path):
        if line.startswith("Patch"):
            cur = int(re.split(r"\s+", line.strip())[1])
        elif cur == want and line.strip()[:1].isdigit():
            rows.append([float(v) for v in line.split(",")])
    return np.atleast_2d(np.array(rows))


print(f"{'t s':>6} {'mean C':>8} {'max C':>8} {'cells>350':>10}")
for f in sorted(glob.glob("wt_*.txt"), key=lambda p: int(re.findall(r"\d+", p)[0])):
    t = int(re.findall(r"\d+", f)[0])
    a = patch_rows(f, 2)
    T = a[:, 3]
    over = int((T > 350).sum())
    print(f"{t:6d} {T.mean():8.0f} {T.max():8.0f} {over:6d}/{len(T)}")
