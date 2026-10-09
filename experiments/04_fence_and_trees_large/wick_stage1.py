"""Stage 1 of the 'wick' case: new domain, bigger garden, house relocated,
and a wooden fence material/surface added.

Domain 60 x 60 x 24 m at 1 m cells (86,400 cells).  Lawn 34 x 24 m so there is
real garden around the house rather than 4-5 m of clearance.
"""
import os
import re

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
s = open(os.path.join(CASE, "garden_tall.fds")).read()

s = re.sub(r"&MESH[^/]*/",
           "&MESH ID='garden', IJK=60,60,24, XB=0,60, 0,60, 0,24 /", s, count=1)
s = s.replace("CHID='garden_tall'", "CHID='wick'")
s = s.replace("T_END=120.", "T_END=160.")

s = s.replace("&VENT XB=16.0,40.0, 12.0,28.0, 0.0,0.0, SURF_ID='LAWN' /",
              "&VENT XB=20.0,54.0, 18.0,42.0, 0.0,0.0, SURF_ID='LAWN' /")
s = s.replace("&VENT XB=1.0,4.0, 18.0,22.0, 0.0,0.0, SURF_ID='SPOT IGN' /",
              "&VENT XB=2.0,6.0, 28.0,32.0, 0.0,0.0, SURF_ID='SPOT IGN' /")

s = s.replace("XB=21.0,33.0, 16.0,24.0, 0.0,3.5",
              "XB=32.0,44.0, 26.0,34.0, 0.0,3.5")
s = s.replace("XB=20.6,33.4, 15.6,24.4, 3.5,5.6",
              "XB=31.6,44.4, 25.6,34.4, 3.5,5.6")
s = s.replace("&VENT XB=21.0,21.0, 17.5,19.0, 1.0,2.2",
              "&VENT XB=32.0,32.0, 27.5,29.0, 1.0,2.2")
s = s.replace("&VENT XB=21.0,21.0, 21.0,22.5, 1.0,2.2",
              "&VENT XB=32.0,32.0, 31.0,32.5, 1.0,2.2")

FENCE = """&MATL ID = 'FENCE WOOD'
      DENSITY       = 500.0
      CONDUCTIVITY  = 0.12
      SPECIFIC_HEAT = 1.7
      EMISSIVITY    = 0.92 /

&RAMP ID='fence_burn', T=  0.0, F=0.0 /
&RAMP ID='fence_burn', T= 10.0, F=1.0 /
&RAMP ID='fence_burn', T=120.0, F=0.7 /
&RAMP ID='fence_burn', T=300.0, F=0.0 /

&SURF ID            = 'FENCE'
      RGB           = 150,110,70
      MATL_ID       = 'FENCE WOOD'
      THICKNESS     = 0.02
      HRRPUA        = 220.0
      IGNITION_TEMPERATURE = 300.0
      RAMP_Q        = 'fence_burn' /

"""
s = s.replace("! --- house body", FENCE + "! --- house body")

open(os.path.join(CASE, "wick.fds"), "w").write(s)
print("mesh:", re.search(r"&MESH[^/]*/", s).group(0))
print("lawn:", "XB=20.0,54.0" in s, " house:", "XB=32.0,44.0" in s)
print("fence surf added:", "ID            = 'FENCE'" in s)
