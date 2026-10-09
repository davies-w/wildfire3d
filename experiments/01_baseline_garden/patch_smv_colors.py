#!/usr/bin/env python3
"""Recolour surfaces in an FDS .smv file, so Smokeview renders them differently.

The .smv is a plain-text description of the case, and Smokeview reads its
surface colours from here.  Patching it recolours a render without re-running
the solver -- handy for identifying which surface an unexplained patch of
colour actually belongs to.

Usage:
    patch_smv_colors.py <case.smv> NAME=R,G,B [NAME=R,G,B ...]

Example -- make GRASS unmistakable:
    patch_smv_colors.py garden_loft.smv GRASS=255,0,255
"""
from __future__ import annotations

import re
import shutil
import sys


def patch(path: str, mapping: dict[str, tuple[int, int, int]]) -> int:
    lines = open(path).read().split("\n")
    out: list[str] = []
    cur: str | None = None
    hits = 0
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() == "SURFACE":
            # a SURFACE block is exactly: SURFACE / NAME / two params / colour
            # / null -- so take the name, and consume this block's colour line
            # with the pointer reset immediately afterwards.
            cur = lines[i + 1].strip() if i + 1 < len(lines) else None
            continue
        if re.match(r"^\s*\d+\s+[\d.E+-]+\s+[\d.E+-]+\s", line) and cur in mapping:
            r, g, b = (v / 255.0 for v in mapping[cur])
            parts = line.split()
            parts[3], parts[4], parts[5] = f"{r:.5f}", f"{g:.5f}", f"{b:.5f}"
            out[-1] = "  " + "      ".join(parts)
            hits += 1
            cur = None          # <- reset per block, not only on a hit
    open(path, "w").write("\n".join(out))
    return hits


def main() -> None:
    path = sys.argv[1]
    mapping = {}
    for spec in sys.argv[2:]:
        name, rgb = spec.split("=")
        mapping[name.strip()] = tuple(int(x) for x in rgb.split(","))
    shutil.copy(path, path + ".orig")
    n = patch(path, mapping)
    print(f"patched {n} surfaces in {path}")
    for k, v in mapping.items():
        print(f"  {k} -> RGB{v}")
    print(f"  (original saved as {path}.orig)")


if __name__ == "__main__":
    main()
