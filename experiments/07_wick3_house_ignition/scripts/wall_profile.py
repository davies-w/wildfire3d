"""Parse the fds2ascii boundary dump and report per-patch temperatures.

The file contains one block per boundary patch, each with its own header:

    Patch   2  18.00<x< 18.00,  8.00<y<16.00,  0.00<z<3.50
     X,Y,Z, WALL TEMPERATURE
     <x>, <y>, <z>, <T in C>
"""
import re

import numpy as np

BLOCKS = {}
cur = None
for line in open("wallT_400.txt"):
    if line.startswith("Patch"):
        cur = int(re.split(r"\s+", line.strip())[1])
        BLOCKS[cur] = []
    elif cur is not None and line.strip()[:1].isdigit():
        BLOCKS[cur].append([float(v) for v in line.split(",")])

for idx, rows in BLOCKS.items():
    a = np.atleast_2d(np.array(rows))
    if a.shape[0] < 1 or a.shape[1] < 4:
        continue
    T, z = a[:, 3], a[:, 2]
    print(f"patch {idx:3d}: {len(T):4d} cells   "
          f"mean {T.mean():7.0f} C   MAX {T.max():7.0f} C")
