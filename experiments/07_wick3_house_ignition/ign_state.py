"""Map every boundary-data patch to its surface, and read temperature per frame.

This is the data source for the ignition animation.  Instead of asking
Smokeview to map a boundary variable onto its own palette -- which rendered the
whole scene blue and never marked the house wall at 1451 C -- we pull the
temperature out of the .bf ourselves.

Patch geometry came from dump_patches.py, not guesswork.  Surfaces overlap in
space (a single fence box would swallow the trunk), so each surface gets
explicit disjoint boxes and the mapping is checked: every patch must belong to
exactly one surface, and the check is printed rather than assumed.

Frame times must be multiples of DT_BNDF (4 s), or fds2ascii returns NaN for a
window that starts off-grid.
"""
import os, re, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import DIST, FDS_ROOT  # noqa: E402

# case name and CHID, so the same tool serves any wick case:
#   python3 ign_state.py wick4 wick4
CASE_NAME = sys.argv[1] if len(sys.argv) > 1 else "wick3"
CHID = sys.argv[2] if len(sys.argv) > 2 else "wick3c"
CASE = os.path.join(FDS_ROOT, "cases", CASE_NAME)
F2A = os.path.join(DIST, "bin/fds2ascii")

# name -> (list of boxes, ignition temperature in C)
SURFACES = {
    "CANOPY": ([(14.49, 10.0, 2.0, 17.51, 16.0, 6.5)], 250.0),
    "TRUNK": ([(15.99, 12.49, 0.0, 17.01, 13.51, 2.01)], 250.0),
    "WOOD WALL": ([(17.99, 8.0, 0.0, 30.01, 16.0, 3.51)], 350.0),
    "ROOF": ([(17.49, 7.49, 3.49, 30.51, 16.51, 5.51)], 550.0),
    "FENCE": ([
        (10.99, 11.49, 0.0, 18.01, 12.01, 2.01),   # spur to the house
        (10.49, 3.49, 0.0, 11.01, 20.51, 2.01),    # run along x = 11
        (10.99, 3.49, 0.0, 31.01, 4.01, 2.01),     # run along y = 4
        (10.99, 19.99, 0.0, 31.01, 20.51, 2.01),   # run along y = 20
    ], 300.0),
}

PATCH = re.compile(r"Patch\s+(\d+)\s+(.*?),\s*(.*?),\s*(.*?)\s*$")
NUM = re.compile(r"(-?\d+\.\d+)\s*<\s*[xyz]\s*<\s*(-?\d+\.\d+)")


def bbox(rest):
    """The three coordinate ranges from a patch description line."""
    out = []
    for part in rest.split(","):
        m = NUM.search(part)
        out.append((float(m.group(1)), float(m.group(2))) if m else None)
    return out


def inside(box, lo_hi):
    """A patch lies inside a box if every coordinate range is contained.

    Boxes are (xlo, ylo, zlo, xhi, yhi, zhi) -- low triplet then high triplet,
    NOT axis-interleaved.
    """
    if any(b is None for b in box):
        return False
    for i in range(3):
        lo, hi = lo_hi[i], lo_hi[i + 3]
        if box[i][0] < lo - 1e-6 or box[i][1] > hi + 1e-6:
            return False
    return True


def surfaces_for(box):
    """Every surface whose declared boxes contain this patch."""
    return [name for name, (boxes, _) in SURFACES.items()
            if any(inside(box, b) for b in boxes)]


def dump(orient, t0):
    """Run fds2ascii for one orientation and one time window."""
    out = "ig_%d_%d.txt" % (t0, orient)
    stdin = "%s\n3\n1\nn\n%d %d\n%d\n1\n1\n%s\n" % (CHID, t0, t0 + 2,
                                                    orient, out)
    subprocess.run([F2A], cwd=CASE, input=stdin, text=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=1800)
    p = os.path.join(CASE, out)
    return p if os.path.exists(p) else None


def check_mapping(t0=0):
    """Every patch in the data, and which surface it maps to.

    A patch matching NO surface means geometry is left uncoloured; one
    matching TWO means a surface's colour would be driven by another's heat.
    Both are reported rather than assumed away.
    """
    rows = []
    for orient in (1, -1, 2, -2, 3, -3):
        p = dump(orient, t0)
        if not p:
            continue
        for line in open(p):
            if not line.startswith("Patch"):
                continue
            m = PATCH.match(line.rstrip())
            if not m:
                continue
            box = bbox(m.group(2) + "," + m.group(3) + "," + m.group(4))
            if any(b is None for b in box):
                continue
            rows.append((orient, box, surfaces_for(box)))
    return rows


def peak_all(t0):
    """Hottest cell in each surface, over one time window.

    One fds2ascii run per orientation serves every surface, so this is 6 runs
    per frame rather than 6 per surface.
    """
    best = {name: None for name in SURFACES}
    for orient in (1, -1, 2, -2, 3, -3):
        p = dump(orient, t0)
        if not p:
            continue
        active = []
        for line in open(p):
            if line.startswith("Patch"):
                m = PATCH.match(line.rstrip())
                active = []
                if m:
                    box = bbox(m.group(2) + "," + m.group(3) + "," + m.group(4))
                    active = surfaces_for(box)
                continue
            if active and "," in line:
                parts = line.split(",")
                if len(parts) >= 4:
                    try:
                        v = float(parts[3])
                    except ValueError:
                        continue
                    for name in active:
                        best[name] = v if best[name] is None else max(best[name], v)
    return best


TIMES = [40, 92, 140, 180, 200, 220, 240, 260, 280, 300, 320, 348]
# a case may want different sample times:
#   python3 ign_state.py wick4 wick4 20,40,60,80,100,120,150,180,220,260,300
if len(sys.argv) > 3:
    TIMES = [int(x) for x in sys.argv[3].split(",")]

if __name__ == "__main__":
    import json

    rows = check_mapping()
    bad = [(o, b, n) for o, b, n in rows if len(n) != 1]
    print("patches: %d   not mapped to exactly one surface: %d"
          % (len(rows), len(bad)))
    for o, b, n in bad:
        print("  o%-3d x%7.2f-%7.2f y%7.2f-%7.2f z%7.2f-%7.2f -> %s"
              % (o, b[0][0], b[0][1], b[1][0], b[1][1], b[2][0], b[2][1],
                 ", ".join(n) if n else "NONE"))

    table = {}
    print("\n%-5s %s" % ("t", "".join("%-19s" % n for n in SURFACES)))
    for t in TIMES:
        vals = peak_all(t)
        table[str(t)] = vals
        print("%-5d %s" % (t, "".join(
            "%-19s" % ("--" if vals[n] is None
                       else "%.0f (ign %.0f)" % (vals[n], SURFACES[n][1]))
            for n in SURFACES)))

    path = os.path.join(CASE, "ign_state.json")
    open(path, "w").write(json.dumps(table, indent=1))
    print("\nwrote %s" % path)
