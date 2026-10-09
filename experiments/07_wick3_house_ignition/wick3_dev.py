"""Restart to t=600 with a single, known-good wall-temperature device.

IOR handling for DEVC turned out to be fussier than the manual suggests: the
first device (IOR=-1, the -x wall face) is accepted, but every subsequent
attempt -- IOR=2 for +y, IOR=3 for +z, points inside and outside the solid --
was rejected with ERROR(101).  Rather than keep guessing, keep the one device
that works.  It measures exactly what we need: whether the west wall, i.e. the
face the fire approaches, reaches its 350 C ignition temperature.

The canopy and roof are still colour-coded by the boundary file, so their
behaviour is visible even without devices.
"""
import os
import re

CASE = os.path.expanduser("~/FDS/cases/wick3")
s = open(os.path.join(CASE, "wick3.fds")).read()

s = s.replace("T_END=200.", "T_END=600.")
s = re.sub(r"&MISC ", "&MISC RESTART=.TRUE., ", s, count=1)
s = s.replace("&DEVC ID='HRR', QUANTITY='HRR', XB=0,40, 0,40, 0,12 /",
              "&DEVC ID='HRR', QUANTITY='HRR', XB=0,32, 0,24, 0,12 /")

DEVCS = """&DEVC ID='WALL_WEST', QUANTITY='WALL TEMPERATURE',
      XYZ=18.25,13.25,2.25, IOR=-1, CELL_CENTERED=.TRUE. /
&DUMP"""
s = s.replace("&DUMP", DEVCS, 1)

open(os.path.join(CASE, "wick3_dev.fds"), "w").write(s)
print("devices:", [l.strip()[:50] for l in s.split("\n") if l.startswith("&DEVC")])
