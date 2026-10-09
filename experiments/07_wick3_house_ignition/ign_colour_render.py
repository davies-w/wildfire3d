"""Render experiment 07's ignition animation from measured data.

The earlier version let Smokeview map the burning-rate boundary file onto its
own palette and then applied a red-versus-blue pixel test to the result.  That
rendered the scene blue and never marked the house wall, even at 1451 C.

Here the colour is a function of the temperature in ign_state.json:

    below a surface's ignition temperature -> its original colour
    at or above                            -> orange, deepening to red

The RGB is written into the .smv SURFACE table and the frame is rendered with
NO boundary file, so Smokeview contributes only geometry, flame, embers and
smoke.  Every colour is printed, so the result can be checked by reading it.

Framing: ZOOM must be applied AFTER SETVIEWPOINT, in a second LOADINIFILE.
Before the viewpoint it is overwritten; measured in try_zoom.py.
"""
import json, os, re, shutil, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402
from ign_state import SURFACES, TIMES  # noqa: E402

CASE = os.path.join(FDS_ROOT, "cases/wick3")
SMV = os.path.join(FDS_ROOT, "bin/smv_quiet")
SMV_FILE = os.path.join(CASE, "wick3c.smv")
SMV_KEEP = os.path.join(CASE, "wick3c.smv.orig")
ZOOM_INI = os.path.join(CASE, "zoom_only.ini")
OUT = "igncol"

# Data volumes: soot (smoke), flame temperature (flame), firebrands (embers).
VOLUMES = ["wick3c_1_1.s3d", "wick3c_1_3.s3d", "wick3c_1.prt5"]

# Original surface colours, as fractions of 255 in the .smv SURFACE table.
BASE = {
    "CANOPY": (40, 90, 35),
    "TRUNK": (105, 78, 52),
    "WOOD WALL": (222, 184, 135),
    "ROOF": (169, 169, 169),
    "FENCE": (150, 110, 70),
}
IGNITED = (235, 70, 20)
SEVERE = (170, 15, 5)
HOTTEST = 1400.0


def colour(name, temp):
    """Original colour below ignition; orange deepening to red above it."""
    ign = SURFACES[name][1]
    if temp is None or temp < ign:
        return BASE[name]
    f = min(1.0, (temp - ign) / (HOTTEST - ign))
    return tuple(round(IGNITED[i] + (SEVERE[i] - IGNITED[i]) * f)
                 for i in range(3))


def patch_smv(mapping):
    """Write RGB into the .smv SURFACE blocks.

    The block is positional: SURFACE / NAME / two params / seven numbers whose
    4th-6th are R,G,B as fractions of 255 / null.
    """
    lines = open(SMV_KEEP, errors="replace").read().split("\n")
    hits = 0
    for i, line in enumerate(lines):
        if line.strip() != "SURFACE":
            continue
        name = lines[i + 1].strip()
        if name not in mapping:
            continue
        parts = lines[i + 3].split()
        if len(parts) < 7:
            continue
        r, g, b = (v / 255.0 for v in mapping[name])
        parts[3], parts[4], parts[5] = "%.5f" % r, "%.5f" % g, "%.5f" % b
        lines[i + 3] = "  " + "      ".join(parts)
        hits += 1
    open(SMV_FILE, "w").write("\n".join(lines))
    return hits


def render_frame(t, tag):
    """One frame: patched colours, flame + embers + smoke, whole scene framed."""
    body = "RENDERDIR\n %s\nUNLOADALL\nLOADINIFILE\n wick3c.ini\n" % OUT
    for f in VOLUMES:
        body += "LOADFILE\n %s\n" % f
    body += "SETVIEWPOINT\n iso_b\n"
    body += "LOADINIFILE\n %s\n" % os.path.basename(ZOOM_INI)
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n %s\n" % (t, tag)
    open(os.path.join(CASE, "wick3c.ssf"), "w").write(body)
    return subprocess.run([SMV, "-runscript", "wick3c"], cwd=CASE,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          stdin=subprocess.DEVNULL, timeout=2400).returncode


if __name__ == "__main__":
    state = json.load(open(os.path.join(CASE, "ign_state.json")))
    if not os.path.exists(SMV_KEEP):
        shutil.copy(SMV_FILE, SMV_KEEP)
    open(ZOOM_INI, "w").write("ZOOM\n1 0.5\n")
    shutil.rmtree(os.path.join(CASE, OUT), ignore_errors=True)
    os.makedirs(os.path.join(CASE, OUT))

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(TIMES)
    print("%-5s %s" % ("t", "  ".join("%-22s" % n for n in SURFACES)))
    for t in TIMES[:limit]:
        temps = state[str(t)]
        mapping = {n: colour(n, temps.get(n)) for n in BASE}
        patch_smv(mapping)
        rc = render_frame(t, "c_%03d" % t)
        print("%-5d %s" % (t, "  ".join(
            "%-22s" % ("%s->%s" % (temps.get(n), mapping[n])) for n in SURFACES)))
        if rc != 0:
            print("   smokeview exit %s" % rc)

    shutil.copy(SMV_KEEP, SMV_FILE)
    print("\nrestored original .smv; frames in %s/%s" % (CASE, OUT))
