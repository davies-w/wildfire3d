"""Move the working area into the repository, leaving a compatibility symlink.

~/FDS holds the FDS engine checkout, the NIST binary distribution, the case
directories and their raw output, and a virtualenv. It belongs under the
project (see FDS/README.md), but around sixty scripts still reference
~/FDS/... by literal path.

So: move the contents, then leave ~/FDS as a symlink to the new location. That
keeps every existing script working while the real tree lives in the repo. The
symlink is a shim and should go once the paths are parameters (AGENTS.md rule 1).

Refuses to run unless the destination is empty apart from its README, so it
cannot silently merge two trees.
"""
import os, shutil, sys

SRC = os.path.expanduser("~/FDS")
DST = os.path.expanduser("~/pi/wildfire3d/FDS")

if os.path.islink(SRC):
    sys.exit("~/FDS is already a symlink -- nothing to do")
if not os.path.isdir(SRC):
    sys.exit("~/FDS does not exist")

existing = [n for n in os.listdir(DST) if n != "README.md"]
if existing:
    sys.exit("destination not empty: %s" % existing[:6])

moved = 0
for name in sorted(os.listdir(SRC)):
    shutil.move(os.path.join(SRC, name), os.path.join(DST, name))
    moved += 1

os.rmdir(SRC)
os.symlink(DST, SRC)

print("moved %d entries into %s" % (moved, DST))
print("~/FDS is now a symlink -> %s" % os.readlink(SRC))
print("\ncontents:")
for n in sorted(os.listdir(DST)):
    print("  %s" % n)
