"""Stage 1 for wick3: shrink the domain to 32 x 24 x 12 m, same 0.5 m cells.

64 x 48 x 24 = 73,728 cells, down from 153,600 -- resolution unchanged, just
less empty wildland.  House, lawn, fence and ignition shifted to suit.
"""
import os
import re

CASE = os.path.expanduser("~/FDS/cases/wick2")
DST = os.path.expanduser("~/FDS/cases/wick3")
os.makedirs(DST, exist_ok=True)

s = open(os.path.join(CASE, "wick2.fds")).read()

s = s.replace("CHID='wick2'", "CHID='wick3'")
s = s.replace("T_END=120.", "T_END=200.")
s = re.sub(r"&MESH[^/]*/",
           "&MESH ID='g', IJK=64,48,24, XB=0,32, 0,24, 0,12 /", s, count=1)
s = s.replace("&DUMP DT_SLCF=2., DT_BNDF=2., DT_HRR=1., DT_PART=2. /",
              "&DUMP DT_SLCF=4., DT_BNDF=4., DT_HRR=1., DT_PART=4.,"
              " DT_RESTART=30. /")

# house + roof + windows, shifted south and west
s = s.replace("XB=24.0,36.0, 16.0,24.0, 0.0,3.5", "XB=18.0,30.0, 8.0,16.0, 0.0,3.5")
s = s.replace("XB=23.6,36.4, 15.6,24.4, 3.5,5.6", "XB=17.6,30.4, 7.6,16.4, 3.5,5.6")
s = s.replace("&VENT XB=24.0,24.0, 17.5,19.0, 1.0,2.2",
              "&VENT XB=18.0,18.0, 9.5,11.0, 1.0,2.2")
s = s.replace("&VENT XB=24.0,24.0, 21.0,22.5, 1.0,2.2",
              "&VENT XB=18.0,18.0, 13.0,14.5, 1.0,2.2")

# lawn and ignition
s = s.replace("&VENT XB=16.0,36.0, 12.0,28.0, 0.0,0.0, SURF_ID='LAWN' /",
              "&VENT XB=11.0,31.0, 4.0,20.0, 0.0,0.0, SURF_ID='LAWN' /")
s = s.replace("&VENT XB=2.0,4.0, 18.0,22.0, 0.0,0.0, SURF_ID='SPOT IGN' /",
              "&VENT XB=0.5,2.5, 10.0,14.0, 0.0,0.0, SURF_ID='SPOT IGN' /")

open(os.path.join(DST, "wick3.fds"), "w").write(s)
print("mesh:", re.search(r"&MESH[^/]*/", s).group(0))
print("DUMP:", [l for l in s.split("\n") if l.startswith("&DUMP")])
