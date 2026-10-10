"""Write a variant of a deck with every &GEOM namelist block dropped.

Why: experiment 08's ember_test deck segfaults at about step 600 on both the old
and the current build.  The recorded suspicion was "&GEOM plus airborne
particles", but a probe with ember generation switched off still crashed, so
that explanation is at best half right.  This strips the &GEOM geometry and
leaves everything else -- the burning grass, the embers, the &OBST house -- so
the geometry can be blamed or cleared on its own.

    python3 probe_geom.py in.fds out.fds NEWCHID
"""
import sys

src, dst, chid = sys.argv[1], sys.argv[2], sys.argv[3]

out, dropping, dropped = [], False, 0
for line in open(src):
    stripped = line.strip()
    if stripped.upper().startswith("&GEOM"):
        dropping, dropped = True, dropped + 1
        continue
    if dropping:
        # A namelist ends on the line whose last non-blank character is /.
        if stripped.endswith("/"):
            dropping = False
        continue
    if stripped.upper().startswith("&HEAD"):
        line = line.replace("CHID='ember_test'", "CHID='%s'" % chid)
    out.append(line)

open(dst, "w").writelines(out)
print("dropped %d &GEOM block(s), wrote %s" % (dropped, dst))
