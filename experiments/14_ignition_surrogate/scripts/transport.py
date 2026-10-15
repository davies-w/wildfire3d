"""Coupled flame/radiation screening, not validation against physical experiments."""
import itertools
import json
from benchmark import ROOT, run, write_json

def make_deck(name,hrr,gap,wind,variant):
    dx=0.5 if variant=='coarse' else 0.25
    early=variant!='reference'
    radiation="&RADI NUMBER_RADIATION_ANGLES=50, TIME_STEP_INCREMENT=6 /" if variant=='radiation' else ''
    return f"""&HEAD CHID='{name}', TITLE='Coupled burner to structure screening' /
&MESH IJK={round(6/dx)},{round(4/dx)},{round(4/dx)}, XB=0,6,0,4,0,4 /
&TIME T_END=30. /
&MISC RND_SEED=1234 /
&WIND SPEED={wind}, DIRECTION=270. /
&REAC FUEL='PROPANE', SOOT_YIELD=0.01 /
&MATL ID='WOOD', DENSITY=500., CONDUCTIVITY=0.12, SPECIFIC_HEAT=1.7 /
&SURF ID='MAIN_WALL', MATL_ID='WOOD', THICKNESS=0.02,
 HRRPUA=100., IGNITION_TEMPERATURE=350. /
&SURF ID='BURNER', HRRPUA={hrr}, TAU_Q=0. /
&OBST XB=3,3.5,1,3,0,2.5, SURF_ID='MAIN_WALL' /
&OBST XB={2-gap},{3-gap},1.5,2.5,0,0.5, SURF_IDS='BURNER','INERT','INERT' /
&VENT MB='XMIN', SURF_ID='OPEN' /
&VENT MB='XMAX', SURF_ID='OPEN' /
&VENT MB='YMIN', SURF_ID='OPEN' /
&VENT MB='YMAX', SURF_ID='OPEN' /
&VENT MB='ZMAX', SURF_ID='OPEN' /
{radiation}
&DEVC ID='ignition_wall', QUANTITY='WALL TEMPERATURE', SURF_ID='MAIN_WALL',
 XB=0,6,0,4,0,4, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE', SETPOINT=350. /
&DEVC ID='burning_wall', QUANTITY='BURNING RATE', SURF_ID='MAIN_WALL',
 XB=0,6,0,4,0,4, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /
{("&CTRL ID='ignition_stop', FUNCTION_TYPE='KILL', INPUT_ID='ignition_wall' /" if early else '')}
&BNDF QUANTITY='WALL TEMPERATURE' /
&BNDF QUANTITY='BURNING RATE' /
&DUMP DT_DEVC=0.05, DT_BNDF=0.5, DT_HRR=0.1, DT_RESTART=100000., SMOKE3D=.FALSE. /
&TAIL /
"""

def main():
    results=[]
    for index,(hrr,gap,wind) in enumerate(itertools.product([800,1600],[0.5,1.0],[0,3])):
        for variant in ['reference','early','radiation','coarse']:
            name=f'transport_{index:02d}_{variant}'
            d=run(name,make_deck(name,hrr,gap,wind,variant),timeout=600,
                  scope='synthetic coupled burner/structure; no vegetation or ember validation')
            d.update(scenario=index,variant=variant,hrr_kW_m2=hrr,gap_m=gap,wind_m_s=wind,
                     scope='synthetic coupled burner/structure; no vegetation or ember validation')
            results.append(d)
            write_json(ROOT/'results'/'transport.json',results)
            if d['status']!='complete': raise SystemExit('Run failed; inspect log')

if __name__=='__main__': main()
