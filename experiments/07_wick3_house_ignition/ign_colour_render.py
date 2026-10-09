"""Render experiment 07's ignition animation from measured data.

The earlier version let Smokeview map the burning-rate boundary file onto its
own palette, then applied a red-versus-blue pixel test to the result.  That
rendered the scene blue and never marked the house wall, even at 1451 C.

Here the colour is a function of the measured temperature:

    below a surface's ignition temperature -> its original colour
    at or above                            -> orange, deepening to red

Each frame gets its own .smv with those colours in the SURFACE table, and all
of them are rendered in ONE Smokeview process using LOADSMV between frames.
Smokeview supplies only geometry, flame, embers and smoke -- no boundary file
is loaded, so it never picks a colour.

Framing: ZOOM must come AFTER SETVIEWPOINT, in a second LOADINIFILE; before it,
it is overwritten (measured in try_zoom.py).  Zoom 1 (0.5) is the only setting
that keeps the whole scene visible, so the white margin is cropped afterwards.
"""
import json, os, shutil, subprocess, sys

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
GIF = os.path.join(FDS_ROOT, "cases/wick3/ignition_data.gif")

# Data volumes: soot (smoke), flame temperature (flame), firebrands (embers).
VOLUMES = ["wick3c_1_1.s3d", "wick3c_1_3.s3d", "wick3c_1.prt5"]

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

# Smoke mass extinction coefficient, m2/kg.  Smokeview's default draws the soot
# volume as a near-opaque mass that hides the geometry completely.  Measured at
# t=300, where every surface is ignited: 2500/1200/600 produced no usable frame,
# 300 leaves 13737 warm (ignited) pixels and still shows the plume as grey haze,
# 0 leaves 11977 and almost no smoke.  300 keeps both.
SMOKEPROP = 300.0

ZOOM_LINE = "ZOOM\n1 0.5\n"
WHITE = 235
INFO_BAR = 34
TITLE_BAR = 20


def colour(name, temp):
    """Original colour below ignition; orange deepening to red above it."""
    ign = SURFACES[name][1]
    if temp is None or temp < ign:
        return BASE[name]
    f = min(1.0, (temp - ign) / (HOTTEST - ign))
    return tuple(round(IGNITED[i] + (SEVERE[i] - IGNITED[i]) * f)
                 for i in range(3))


def frame_colours(temps):
    return {n: colour(n, temps.get(n)) for n in BASE}


def variant_smv(mapping, path):
    """A copy of the .smv with this frame's surface colours written in.

    The SURFACE block is positional: SURFACE / NAME / two params / seven
    numbers whose 4th-6th are R,G,B as fractions of 255 / null.
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
    open(path, "w").write("\n".join(lines))
    return hits


def render_one(t, temps):
    """One frame in its own Smokeview process, with this frame's colours.

    The colours must go into the case's own wick3c.smv.  A side-car .smv loaded
    with LOADSMV is ignored for surface colours -- verified by patching
    fr_300.smv correctly and still seeing the base green rendered.
    """
    variant_smv(frame_colours(temps), SMV_FILE)
    body = "RENDERDIR\n %s\nUNLOADALL\nLOADINIFILE\n wick3c.ini\n" % OUT
    for f in VOLUMES:
        body += "LOADFILE\n %s\n" % f
    body += "SETVIEWPOINT\n iso_b\nLOADINIFILE\n %s\nSMOKEPROP\n %g\n"
    body = body % (os.path.basename(ZOOM_INI), SMOKEPROP)
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n c_%03d\n" % (t, t)
    open(os.path.join(CASE, "wick3c.ssf"), "w").write(body)
    return subprocess.run([SMV, "-runscript", "wick3c"], cwd=CASE,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          stdin=subprocess.DEVNULL, timeout=2400).returncode


def white_box(paths, pad=6):
    """Common crop box trimming the white margin.

    ZOOM 1 (0.5) is the only setting that keeps the whole scene visible, which
    leaves a lot of white.  Cropping tightens the frame without cutting any
    geometry, since the mesh box is drawn.  One box is shared by every frame so
    the animation does not jitter.
    """
    import numpy as np
    from PIL import Image

    lo_x = lo_y = 10 ** 9
    hi_x = hi_y = -1
    w = h = 0
    for p in paths:
        a = np.asarray(Image.open(p).convert("RGB"), dtype=int)
        body = a.min(axis=2) <= WHITE
        body[a.shape[0] - INFO_BAR:, :] = False
        body[:TITLE_BAR, :] = False
        ys, xs = np.nonzero(body)
        h, w = a.shape[0] - INFO_BAR, a.shape[1]
        if not len(ys):
            continue
        lo_y, hi_y = min(lo_y, ys.min()), max(hi_y, ys.max())
        lo_x, hi_x = min(lo_x, xs.min()), max(hi_x, xs.max())
    return (max(0, lo_x - pad), max(0, lo_y - pad),
            min(w, hi_x + pad), min(h, hi_y + pad))


def show(v):
    return "--" if v is None else "%.0f" % v


if __name__ == "__main__":
    state = json.load(open(os.path.join(CASE, "ign_state.json")))
    if not os.path.exists(SMV_KEEP):
        shutil.copy(SMV_FILE, SMV_KEEP)
    open(ZOOM_INI, "w").write(ZOOM_LINE)

    out = os.path.join(CASE, OUT)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)

    # one .smv per frame, carrying that frame's colours
    print("%-5s %s" % ("t", "  ".join("%-21s" % n for n in SURFACES)))
    for t in TIMES:
        temps = state[str(t)]
        mapping = frame_colours(temps)
        variant_smv(mapping, os.path.join(CASE, "fr_%03d.smv" % t))
        print("%-5d %s" % (t, "  ".join(
            "%-21s" % ("%s->%s" % (show(temps.get(n)), mapping[n]))
            for n in SURFACES)))

    # One launch per frame.  Rendering all frames in a single process via
    # LOADSMV was tried and does not work: changing the surface colours means
    # re-reading the .smv, and after the first LOADSMV the data volumes stop
    # reloading, so 10 of 12 frames came out blank (verified by md5).
    # Smokeview also segfaults on the occasional frame, so retry what is
    # missing -- one crash must not silently cost a frame of animation.
    for round_ in (1, 2):
        for t in TIMES:
            p = os.path.join(out, "c_%03d.png" % t)
            if os.path.exists(p):
                continue
            rc = render_one(t, state[str(t)])
            print("  pass %d  t=%-4d exit %-4s %s"
                  % (round_, t, rc, "ok" if os.path.exists(p) else "STILL MISSING"))

    paths = [os.path.join(out, "c_%03d.png" % t) for t in TIMES]
    paths = [p for p in paths if os.path.exists(p)]
    print("rendered %d of %d frames" % (len(paths), len(TIMES)))

    from PIL import Image
    box = white_box(paths)
    for p in paths:
        Image.open(p).convert("RGB").crop(box).save(p)
    ims = [Image.open(p).convert("RGB") for p in paths]
    ims[0].save(GIF, save_all=True, append_images=ims[1:], duration=600, loop=0)
    print("%s\n  %d frames, %d bytes" % (GIF, len(ims), os.path.getsize(GIF)))
