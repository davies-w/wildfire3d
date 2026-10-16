from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parent
base=(ROOT/'inputs/legacy_lot.fds').read_text()
# Strip legacy prose to avoid retaining stale geometry descriptions.
base='\n'.join(x for x in base.splitlines() if not x.lstrip().startswith('!'))+'\n'
base=re.sub(r"&SURF ID='GLASS'.*?/", "&MATL ID='INERT GLASS', CONDUCTIVITY=1.0, SPECIFIC_HEAT=0.84, DENSITY=2500. /\n&SURF ID='GLASS', MATL_ID='INERT GLASS', THICKNESS=0.006 /",base,flags=re.S)
base=re.sub(r'&DUMP.*?/', '&DUMP DT_SLCF=10., DT_BNDF=10., DT_HRR=1., DT_DEVC=0.5, DT_PART=30., DT_RESTART=100000., SMOKE3D=.FALSE. /',base,flags=re.S)
base=base.replace("&DEVC ID='HRR', QUANTITY='HRR', XB=0,40, 0,40, 0,12 /", "&DEVC ID='HRR', QUANTITY='HRR', XB=0,32,0,24,0,12 /\n&DEVC ID='house_wall_max', QUANTITY='WALL TEMPERATURE', SURF_ID='WOOD WALL', XB=17,31,7,17,0,6, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /\n&DEVC ID='house_roof_max', QUANTITY='WALL TEMPERATURE', SURF_ID='ROOF', XB=17,31,7,17,0,6, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /\n&DEVC ID='house_ignition_wall', QUANTITY='WALL TEMPERATURE', SURF_ID='WOOD WALL', XB=17,31,7,17,0,6, SPATIAL_STATISTIC='MAX', SETPOINT=350., INITIAL_STATE=.FALSE. /\n&DEVC ID='house_ignition_roof', QUANTITY='WALL TEMPERATURE', SURF_ID='ROOF', XB=17,31,7,17,0,6, SPATIAL_STATISTIC='MAX', SETPOINT=550., INITIAL_STATE=.FALSE. /")
hot="\n&SURF ID='EXPOSURE', HRRPUA=600., TAU_Q=0. /\n&OBST XB=16,17,8,10,0,0.5, SURF_IDS='EXPOSURE','INERT','INERT' /\n"
manifest=[]
configs=[('smoke',8,False,True,'baseline'),('lot_a',30,False,False,'baseline'),('lot_profile',30,False,True,'baseline'),('lot_b',30,False,False,'baseline'),('hot_profile',30,True,True,'baseline'),('hot_a',30,True,False,'baseline'),('hot_passive',30,True,False,'passive'),('hot_radiation',30,True,False,'radiation'),('hot_coarse',30,True,False,'coarse'),('lot_full',600,False,True,'baseline')]
for name,end,heated,profile,variant in configs:
 s=(ROOT/'inputs/smoke.fds').read_text() if name=='smoke' else base
 s=re.sub(r"CHID='[^']+'",f"CHID='{name}'",s);s=re.sub(r'T_END=[\d.]+',f'T_END={end}.',s)
 if heated:s=s.replace('&TAIL /',hot+'&TAIL /')
 if variant=='radiation':s=s.replace('&TAIL /','&RADI NUMBER_RADIATION_ANGLES=50, TIME_STEP_INCREMENT=6 /\n&TAIL /')
 if variant=='coarse':s=s.replace('IJK=64,48,24','IJK=32,24,12')
 # Reproducible random seed, including ember generation.
 s=s if 'RND_SEED=' in s else s.replace('&MISC ', '&MISC RND_SEED=1234, ',1)
 (ROOT/'decks'/f'{name}.fds').write_text(s)
 manifest.append(dict(case=name,horizon_s=end,profile=profile,variant=variant,heated=heated,cells=8192 if name=='smoke' else 9216 if variant=='coarse' else 73728,deck_sha256=hashlib.sha256(s.encode()).hexdigest()))
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
