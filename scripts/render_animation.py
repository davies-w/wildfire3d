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
import case_config  # noqa: E402

if len(sys.argv) < 2:
    sys.exit("usage: render_animation.py <render.json> [smokeprop]")
CONFIG = case_config.load(sys.argv[1])
CASE = CONFIG["case_dir"]
CHID = CONFIG["chid"]
TIMES = CONFIG["times"]
OUT = CONFIG["out_dir"]
SMV = os.path.join(FDS_ROOT, "bin/smv_quiet")
SMV_FILE = CONFIG["smv"]
SMV_KEEP = CONFIG["smv_keep"]
GIF = CONFIG["gif"]
VOLUMES = CONFIG["volumes"]

# surface name -> original RGB, from the config
BASE = {name: tuple(s["rgb"]) for name, s in CONFIG["surfaces"].items()}
# surface name -> (boxes, ignition temperature)
SURFACES = {name: (s["boxes"], float(s["ignition"]))
            for name, s in CONFIG["surfaces"].items()}

IGNITED = (235, 70, 20)
SEVERE = (170, 15, 5)
HOTTEST = 1400.0

# Smoke mass extinction coefficient, m2/kg.  Smokeview's default draws the soot
# volume as a near-opaque mass that hides the geometry.  The right value is
# case-specific: a smaller fire has a fainter plume, so it needs a larger
# coefficient to read.  Set in the config, overridable here for a sweep.
SMOKEPROP = float(sys.argv[2]) if len(sys.argv) > 2 else CONFIG["smokeprop"]

ZOOM_INI = CONFIG["view_ini"]
# Viewpoint zoom.  1.0 is Smokeview's default and clips the foreground; 0.5
# frames the whole scene while keeping iso_b's orientation.
VIEW_ZOOM = 0.5


def make_view_ini():
    """Copy the case .ini with iso_b's zoom reduced.

    ZOOM must not be applied as a separate keyword after SETVIEWPOINT: a second
    LOADINIFILE resets the camera and silently replaces the 3/4 iso view with a
    flat side view.  The zoom is a field of the viewpoint itself -- eye_x, eye_y,
    eye_z, zoom, zoomindex on the line after eyeview,rotation_index,view_id -- so
    it is edited there, preserving azimuth -45 and elevation 25.
    """
    lines = open(os.path.join(CASE, CHID + ".ini"), errors="replace").read().split("\n")
    for i, line in enumerate(lines):
        if line.strip() != "VIEWPOINT5":
            continue
        if i + 12 >= len(lines) or lines[i + 12].strip() != "iso_b":
            continue
        eye = lines[i + 2].split()
        eye[3] = "%.6f" % VIEW_ZOOM          # zoom
        eye[4] = "%d" % (1 if VIEW_ZOOM == 0.5 else 2)   # zoom index
        lines[i + 2] = " " + " ".join(eye)
    open(ZOOM_INI, "w").write("\n".join(lines))
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
    shutil.copy(SMV_FILE, os.path.join(CASE, "fr_%03d.smv" % t))
    body = "RENDERDIR\n %s\nUNLOADALL\nLOADINIFILE\n %s\n" % (
        OUT, os.path.basename(ZOOM_INI))
    for f in VOLUMES:
        body += "LOADFILE\n %s\n" % f
    body += "SETVIEWPOINT\n iso_b\n"
    body += "SMOKEPROP\n %g\n" % SMOKEPROP
    body += "SETTIMEVAL\n %d.0\nRENDERONCE\n c_%03d\n" % (t, t)
    open(os.path.join(CASE, CHID + ".ssf"), "w").write(body)
    return subprocess.run([SMV, "-runscript", CHID], cwd=CASE,
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


def remove_outline(path, thresh=20, grow=2):
    """Erase Smokeview's mesh boundary box from a rendered frame.

    There is no script command for it: the `o` key cycles 1 current mesh /
    2 whole case / 3 none, but KEYBOARD in a batch run has no effect (three
    presses changed nothing).  So the lines are inpainted out instead.

    Safe because the lines are near-pure black (1.48% of the frame) and
    nothing else in these scenes is that dark -- the darkest geometry is the
    roof's shadowed side at mid grey.  Pixels below `thresh` are taken as the
    line, grown to catch the antialiased fringe, and replaced with the median
    of the untouched pixels around them.
    """
    import numpy as np
    from PIL import Image

    im = Image.open(path).convert("RGB")
    a = np.asarray(im, int)
    m = a.max(axis=2) < thresh
    if not m.any():
        return 0
    for _ in range(grow):
        m = (m | np.roll(m, 1, 0) | np.roll(m, -1, 0)
             | np.roll(m, 1, 1) | np.roll(m, -1, 1))
    out = a.copy()
    for y, x in zip(*np.nonzero(m)):
        y0, y1 = max(0, y - 3), min(a.shape[0], y + 4)
        x0, x1 = max(0, x - 3), min(a.shape[1], x + 4)
        good = a[y0:y1, x0:x1][~m[y0:y1, x0:x1]]
        out[y, x] = np.median(good, axis=0) if len(good) else 255
    Image.fromarray(out.astype(np.uint8)).save(path)
    return int(m.sum())


def add_timebar(path, t, t_end):
    """Draw a progress bar along the bottom, so the animation shows its time.

    The bar fills from left to right as t approaches t_end, with the times
    written beside it.  Kept in the image rather than inferred from the frame
    order, so a single exported frame still says when it is.
    """
    from PIL import Image, ImageDraw

    im = Image.open(path).convert("RGB")
    w, h = im.size
    canvas = Image.new("RGB", (w, h + 24), (255, 255, 255))
    canvas.paste(im, (0, 0))
    d = ImageDraw.Draw(canvas)
    y0, y1 = h + 4, h + 13
    d.rectangle([8, y0, w - 9, y1], outline=(110, 110, 110))
    frac = 0.0 if not t_end else max(0.0, min(1.0, t / float(t_end)))
    x = 8 + int((w - 18) * frac)
    if x > 8:
        d.rectangle([8, y0, x, y1], fill=(230, 90, 20))
    d.text((9, h + 12), "t = %d s  of  %d s" % (t, t_end), fill=(20, 20, 20))
    canvas.save(path)


def show(v):
    return "--" if v is None else "%.0f" % v


if __name__ == "__main__":
    state = json.load(open(os.path.join(CASE, "ign_state.json")))
    if not os.path.exists(SMV_KEEP):
        shutil.copy(SMV_FILE, SMV_KEEP)
    make_view_ini()

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
    # the mesh boundary box cannot be switched off from the script, so it is
    # painted out before the frame is cropped
    if not CONFIG.get("show_outline", False):
        for p in paths:
            remove_outline(p)

    box = white_box(paths)
    t_end = max(TIMES)
    for p, t in zip(paths, [t for t in TIMES
                            if os.path.exists(os.path.join(out, "c_%03d.png" % t))]):
        Image.open(p).convert("RGB").crop(box).save(p)
        add_timebar(p, t, t_end)
    ims = [Image.open(p).convert("RGB") for p in paths]
    ims[0].save(GIF, save_all=True, append_images=ims[1:], duration=600, loop=0)
    print("%s\n  %d frames, %d bytes" % (GIF, len(ims), os.path.getsize(GIF)))
