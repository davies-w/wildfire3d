"""Rewrite a deck's &GEOM canopy blocks as &OBST boxes, keeping other &GEOMs.

Why: experiment 08's ember_test.fds segfaults at about step 600 on both engine
builds. Dropping all six &GEOM blocks makes it run to completion, and switching
off firebrand generation does not, so the geometry is the cause. Experiment 03's
garden_veg keeps a &GEOM gable roof and runs to completion with embers, so only
the &GEOM canopies are converted here and the roof is left alone.

The trade: a pyramid canopy becomes its bounding box, the same trade
garden_veg_obst already makes for its trees. Any &GEOM (not just canopies) is
converted, because in this deck the gable *roof* is what triggers the segfault:
converting only the five canopies still crashed, and dropping the roof as well
let it run to t=40 s. Experiment 03's garden_veg keeps its &GEOM roof and runs
fine, so this is deck-specific, not a blanket "&GEOM is broken".

    python3 geom_canopies_to_obst.py in.fds out.fds NEWCHID
"""
import re, sys

src, dst, chid = sys.argv[1], sys.argv[2], sys.argv[3]
convert_all = "--all" in sys.argv
lines = open(src).readlines()
out, i, converted = [], 0, 0
while i < len(lines):
    m = re.match(r"\s*&GEOM\s+ID='([A-Za-z0-9_]+)'\s*,\s*SURF_ID='([A-Za-z0-9_ ]+)'",
                 lines[i], re.I)
    if m and (m.group(1).upper().startswith("CANOPY") or convert_all):
        block = [lines[i]]
        i += 1
        while not block[-1].strip().endswith("/"):
            block.append(lines[i])
            i += 1
        text = "".join(block)
        verts = text.split("VERTS=")[1].split("FACES=")[0]
        verts = re.sub(r"!.*", "", verts)
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", verts)]
        xyz = list(zip(*[iter(nums)] * 3))
        lo = [min(p[k] for p in xyz) for k in range(3)]
        hi = [max(p[k] for p in xyz) for k in range(3)]
        out.append("&OBST XB=%.1f,%.1f, %.1f,%.1f, %.1f,%.1f, SURF_ID='%s' /\n"
                   % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], m.group(2)))
        converted += 1
        continue
    if lines[i].strip().upper().startswith("&HEAD"):
        line = lines[i].replace("CHID='ember_test'", "CHID='%s'" % chid)
        out.append(line)
        i += 1
        continue
    out.append(lines[i])
    i += 1

open(dst, "w").writelines(out)
print("converted %d &GEOM canopy block(s) to &OBST, wrote %s" % (converted, dst))
