"""Build the no-ladder-tree case from experiment 07's deck.

Control for experiment 07: identical in every respect except that the ladder
tree under the fence spur is gone.  That tree's canopy sits directly over the
spur (`XB=14.5,17.5, 10.0,16.0, 1.8,6.5`), so its removal tests how much of the
house ignition came from the fence alone versus the fence plus a tree in
contact with it.

Deriving the deck in code rather than copying it makes the single difference
explicit and impossible to get subtly wrong.

    python3 build_wick4.py
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

SRC = os.path.join(_d, "experiments", "07_wick3_house_ignition", "wick3c.fds")
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "wick4.fds")

# the ladder tree: trunk and canopy, identified by their spans
DROP = ("XB=16.0,17.0, 12.5,13.5", "XB=14.5,17.5, 10.0,16.0")

src = open(SRC).read()
src = src.replace("CHID='wick3c'", "CHID='wick4'")
src = src.replace("TITLE='Refined wick", "TITLE='Wick3c without the ladder tree")
src = src.replace("T_END=350.", "T_END=300.")

kept, dropped = [], 0
for line in src.split("\n"):
    if line.lstrip().startswith("&OBST") and any(d in line for d in DROP):
        dropped += 1
        continue
    # the comment block describing the removed tree no longer applies
    if line.startswith("! --- LADDER TREE"):
        kept.append("! --- LADDER TREE REMOVED: this is the control case ------------")
        continue
    if line.startswith("! The canopy spans x 20.5-23.5"):
        continue
    if line.startswith("! house wall at x=24."):
        continue
    kept.append(line)

open(DST, "w").write("\n".join(kept))
print("wrote %s" % DST)
print("  removed %d obstruction lines (the ladder tree)" % dropped)
for line in kept:
    if line.startswith("&TIME") or line.startswith("&HEAD"):
        print("  " + line)
