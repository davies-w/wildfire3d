"""Read the ladder tree's surface temperature and burning rate from the bf data.

Settles whether the canopy beside the house actually fails to ignite (a physics
result) or ignites and the blend fails to show it (a rendering bug).

fds2ascii selects BNDF data by face orientation and lists patches per run.
Variable 1 is WALL TEMPERATURE, variable 2 is BURNING RATE.  This dumps every
orientation, keeps the patches lying on the canopy (x 14.5-17.5, y 10-16,
z 2-6.5), and reports mean/max per time window, with the house west wall
(x=18, y 8-16, z 0-3.5) alongside for reference.
"""
import os, re, subprocess

CASE = os.path.expanduser("~/FDS/cases/wick3")
F2A = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/bin/fds2ascii")
WINDOWS = [100, 200, 248, 300, 348]

PATCH = re.compile(r"Patch\s+(\d+)\s+(.*?),\s*(.*?),\s*(.*?)\s*$")
NUM = re.compile(r"(-?\d+\.\d+)\s*<\s*[xyz]\s*<\s*(-?\d+\.\d+)")


def bbox(rest):
    out = []
    for part in rest.split(","):
        m = NUM.search(part)
        out.append((float(m.group(1)), float(m.group(2))) if m else None)
    return out


def inside(box, lo, hi, tol=0.01):
    return all(b is not None and b[0] >= lo[i] - tol and b[1] <= hi[i] + tol
               for i, b in enumerate(box))


def dump(orient, var, tag, t0):
    out = "p_%s_%03d.txt" % (tag, t0)
    stdin = "wick3c\n3\n1\nn\n%d %d\n%d\n1\n%d\n%s\n" % (t0, t0 + 2, orient, var, out)
    subprocess.run([F2A], cwd=CASE, input=stdin, text=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
    p = os.path.join(CASE, out)
    return p if os.path.exists(p) else None


def collect(t0, var, want_lo, want_hi):
    vals = []
    for orient in (1, -1, 2, -2, 3, -3):
        p = dump(orient, var, "o%dv%d" % (orient, var), t0)
        if not p:
            continue
        cur = None
        for line in open(p):
            if line.startswith("Patch"):
                m = PATCH.match(line.rstrip())
                cur = bbox(m.group(2) + "," + m.group(3) + "," + m.group(4)) if m else None
                if cur and not inside(cur, want_lo, want_hi):
                    cur = None
                continue
            if cur and "," in line:
                parts = line.split(",")
                if len(parts) >= 4:
                    try:
                        vals.append(float(parts[3]))
                    except ValueError:
                        pass
    return vals


CANOPY_LO, CANOPY_HI = (14.49, 10.0, 2.0), (17.51, 16.0, 6.5)
WALL_LO, WALL_HI = (17.99, 8.0, 0.0), (18.01, 16.0, 3.5)

for t0 in WINDOWS:
    wt = collect(t0, 1, CANOPY_LO, CANOPY_HI)
    br = collect(t0, 2, CANOPY_LO, CANOPY_HI)
    hw = collect(t0, 1, WALL_LO, WALL_HI)
    print("t=%3d  canopy: n=%3d  WT mean %7.1f  max %7.1f   BR max %.5f   |  house wall WT max %7.1f"
          % (t0, len(wt),
             (sum(wt) / len(wt)) if wt else float("nan"),
             max(wt) if wt else float("nan"),
             max(br) if br else 0.0,
             max(hw) if hw else float("nan")))
