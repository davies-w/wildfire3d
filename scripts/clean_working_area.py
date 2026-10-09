"""Remove from ~/FDS the scripts that now live in the repository.

Deletes a loose script ONLY if a file of the same name exists somewhere in the
repo -- so nothing is lost that has not been copied in.  Anything without a
counterpart is left alone and reported, to be classified rather than dropped.
"""
import os

FDS = os.path.expanduser("~/FDS")
REPO = os.path.expanduser("~/pi/wildfire3d")

have = set()
for dp, _, fn in os.walk(REPO):
    if ".git" in dp:
        continue
    for f in fn:
        have.add(f)

removed, kept = [], []
for f in sorted(os.listdir(FDS)):
    if not f.endswith(".py"):
        continue
    if f in have:
        os.remove(os.path.join(FDS, f))
        removed.append(f)
    else:
        kept.append(f)

print("removed %d scripts from ~/FDS" % len(removed))
print("\nstill loose (no counterpart in the repo):")
for f in kept:
    print("  %s" % f)
