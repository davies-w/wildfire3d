#!/usr/bin/env python3
"""Strip the TERRAIN block from an FDS .smv file.

WHY THIS EXISTS
---------------
Smokeview draws the .ter terrain surface with its own colour, chosen outside
the SURFACE table.  It therefore ignores every surface property, and it shows
through wherever an obstruction punches the ground vents -- producing an olive
"skirt" at the base of the house and every tree, which is easily mistaken for
geometry.

Removing the two-line block

    TERRAIN     1
     <case>_1.ter

makes the ground draw from the SURFACE table instead, so surface colours behave
as specified.  The .ter FILE must stay on disk -- deleting it breaks rendering.

IMPORTANT: FDS regenerates the .smv on every solve, so this is a POST-SOLVE
step.  Run it after any re-solve, before rendering.

Usage:
    strip_terrain.py <case_dir> <casename>
or  strip_terrain.py <case_dir>            (casename = dir basename)
"""
import os
import sys


def strip(case_dir: str, casename: str) -> None:
    path = os.path.join(case_dir, f"{casename}.smv")
    if not os.path.exists(path):
        raise SystemExit(f"no such file: {path}")

    lines = open(path).read().split("\n")
    out, i, removed = [], 0, 0
    while i < len(lines):
        if lines[i].startswith("TERRAIN"):
            i += 2                     # the TERRAIN line and its filename
            removed += 1
            continue
        out.append(lines[i])
        i += 1

    if removed:
        open(path, "w").write("\n".join(out))
    print(f"{os.path.basename(path)}: removed {removed} TERRAIN block(s)")
    print("  TERRAIN still present:",
          any(l.startswith("TERRAIN") for l in out))


if __name__ == "__main__":
    case_dir = os.path.expanduser(sys.argv[1])
    casename = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(
        case_dir.rstrip("/"))
    strip(case_dir, casename)
