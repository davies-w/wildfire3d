import os

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
p = os.path.join(CASE, "wick.fds")
s = open(p).read()

spur = "&OBST XB=20.0,32.0, 29.0,30.0, 0.0,1.8, SURF_ID='FENCE', BNDF_OBST=.TRUE. /"
tree = """
! Flammable tree hard against the house, beside the burning fence spur.
! Canopy starts at 2.5 m so the 1.8 m fence flame reaches the trunk, and its
! east face stops 0.1 m short of the roof at x=31.6 (no obstruction overlap).
&OBST XB=29.5,30.5, 31.0,32.0, 0.0,2.5, SURF_ID='TRUNK', BNDF_OBST=.TRUE. /
&OBST XB=27.5,31.5, 28.5,34.5, 2.5,7.5, SURF_ID='CANOPY', BNDF_OBST=.TRUE. /"""

assert spur in s, "spur line not found"
s = s.replace(spur, spur + tree)
open(p, "w").write(s)

print("trees now:", s.count("SURF_ID='TRUNK'"))
print("canopies:", s.count("SURF_ID='CANOPY'"))
print("bndf obstructions:", s.count("BNDF_OBST=.TRUE."))
