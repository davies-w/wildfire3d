"""Stage A: header, materials and surfaces for the refined 'wick' case.

40 x 40 x 12 m at 0.5 m cells = 153,600 cells.  Halving the cell size refines
the fence flame and makes the fence one cell (0.5 m) thick instead of one metre.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os

L = []
A = L.append
A("&HEAD CHID='wick2', TITLE='Refined wick: 0.5 m cells, thin fence' /")
A("&MESH ID='g', IJK=80,80,24, XB=0,40, 0,40, 0,12 /")
A("&TIME T_END=120. /")
A("&MISC BNDF_DEFAULT=.FALSE., LEVEL_SET_MODE=4, CFL_MAX=0.8 /")
A("&WIND SPEED=6.0, DIRECTION=270.0 /")
A("&SPEC ID='WOOD FUEL VAPOR', C=3.4, H=6.2, O=2.5 /")
A("&SPEC ID='WATER VAPOR' /")
A("&REAC FUEL='WOOD FUEL VAPOR', SOOT_YIELD=0.02, HEAT_OF_COMBUSTION=17260. /")
A("")
A("&SURF ID='GRASS', DEFAULT=.TRUE., RGB=138,129,62,")
A("      VEG_LSET_ROS_00=0.08, VEG_LSET_SIGMA=11400., VEG_LSET_BETA=0.0012,")
A("      VEG_LSET_HT=0.5, VEG_LSET_SURF_LOAD=0.2, VEG_LSET_CHAR_FRACTION=0.2,")
A("      VEG_LSET_FIREBASE_TIME=18.0, HRRPUA=30., EMBER_YIELD=0.01,")
A("      EMBER_TRACKING_RATIO=500., PART_ID='brands' /")
A("")
A("&SURF ID='LAWN', RGB=96,160,64, VEG_LSET_ROS_00=0.02, VEG_LSET_SIGMA=14000.,")
A("      VEG_LSET_BETA=0.0008, VEG_LSET_HT=0.08, VEG_LSET_SURF_LOAD=0.06,")
A("      VEG_LSET_FIREBASE_TIME=30.0, HRRPUA=12. /")
A("")
A("&MATL ID='WOOD', CONDUCTIVITY=0.12, SPECIFIC_HEAT=1.7, DENSITY=500. /")
A("&SURF ID='WOOD WALL', RGB=222,184,135, MATL_ID='WOOD', THICKNESS=0.02,")
A("      HRRPUA=200., IGNITION_TEMPERATURE=350., RAMP_Q='wood_burn' /")
A("&SURF ID='ROOF', RGB=169,169,169, MATL_ID='WOOD', THICKNESS=0.02,")
A("      HRRPUA=100., IGNITION_TEMPERATURE=550., RAMP_Q='roof_burn' /")
A("&SURF ID='GLASS', RGB=173,216,230, MATL_ID='WOOD', THICKNESS=0.006,")
A("      HRRPUA=50., IGNITION_TEMPERATURE=180., RAMP_Q='roof_burn' /")
A("&RAMP ID='wood_burn', T=0., F=0. / &RAMP ID='wood_burn', T=30., F=1. /")
A("&RAMP ID='wood_burn', T=300., F=0.8 / &RAMP ID='wood_burn', T=600., F=0.3 /")
A("&RAMP ID='roof_burn', T=0., F=0. / &RAMP ID='roof_burn', T=60., F=1. /")
A("&RAMP ID='roof_burn', T=600., F=0.2 /")
A("")
A("&SURF ID='FENCE', RGB=150,110,70, MATL_ID='WOOD', THICKNESS=0.02,")
A("      HRRPUA=220., IGNITION_TEMPERATURE=300., RAMP_Q='fence_burn' /")
A("&RAMP ID='fence_burn', T=0., F=0. / &RAMP ID='fence_burn', T=10., F=1. /")
A("&RAMP ID='fence_burn', T=120., F=0.7 / &RAMP ID='fence_burn', T=300., F=0. /")
A("")
A("&MATL ID='VEG', DENSITY=15., CONDUCTIVITY=0.08, SPECIFIC_HEAT=1.8 /")
A("&SURF ID='TRUNK', RGB=105,78,52, MATL_ID='WOOD', THICKNESS=0.05,")
A("      HRRPUA=150., IGNITION_TEMPERATURE=350., RAMP_Q='veg_burn' /")
A("&SURF ID='CANOPY', RGB=40,90,35, MATL_ID='VEG', THICKNESS=0.15,")
A("      HRRPUA=400., IGNITION_TEMPERATURE=250., RAMP_Q='veg_burn' /")
A("&RAMP ID='veg_burn', T=0., F=0. / &RAMP ID='veg_burn', T=8., F=1. /")
A("&RAMP ID='veg_burn', T=45., F=0.8 / &RAMP ID='veg_burn', T=150., F=0. /")
A("")
A("&MATL ID='CHAR', DENSITY=110., CONDUCTIVITY=0.1, EMISSIVITY=1.,")
A("      SPECIFIC_HEAT=10000. /")
A("&SURF ID='firebrand', MATL_ID='CHAR', THICKNESS=0.0005, LENGTH=0.005,")
A("      WIDTH=0.005, HEAT_TRANSFER_COEFFICIENT=20., GEOMETRY='CARTESIAN' /")
A("&PART ID='brands', DRAG_LAW='DISK', SURF_ID='firebrand', COLOR='ORANGE',")
A("      INITIAL_TEMPERATURE=800., AGE=60., QUANTITIES='PARTICLE TEMPERATURE' /")
A("&SURF ID='SPOT IGN', VEG_LSET_IGNITE_TIME=0.0, COLOR='RED' /")

open(os.path.join(FDS_ROOT, "cases/wick2/wick2.fds"), "w").write("\n".join(L) + "\n")
print("stage A lines:", len(L))
