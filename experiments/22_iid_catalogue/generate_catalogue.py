"""Generate review-only input definitions. Does not run FDS or generate outcome labels."""
import json,math,hashlib,collections
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point
from shapely.affinity import rotate,translate
R=Path(__file__).resolve().parent;OUT=R/'data';OUT.mkdir(exist_ok=True)
SEED=221018;rng=np.random.default_rng(SEED)
TYPES=[dict(id='N',name='Narrow cone',shape='CONE',radius=[1.5,2.5],height=[8,12],base=[2,4]),dict(id='B',name='Broad cone',shape='CONE',radius=[3,4],height=[4,7],base=[2,4]),dict(id='C',name='Columnar crown',shape='CYLINDER',radius=[2,3],height=[9,13],base=[2,4])]
BUILDINGS=['rectangle','L','courtyard']
def rounded(x):return round(float(x),3)
def tree(kind=None):
 t=TYPES[int(rng.integers(3))] if kind is None else TYPES[kind]
 return dict(type=t['id'],shape=t['shape'],radius=rounded(rng.uniform(*t['radius'])),height=rounded(rng.uniform(*t['height'])),base=rounded(rng.uniform(*t['base'])),moisture=rounded(rng.uniform(.06,.30)),dry_fuel_density_scale=rounded(rng.uniform(.7,1.3)))
def building(kind):
 w,d=rng.uniform(8,12),rng.uniform(8,12)
 if kind=='rectangle':v=[(0,0),(w,0),(w,d),(0,d)]
 elif kind=='L':v=[(0,0),(w,0),(w,.45*d),(.45*w,.45*d),(.45*w,d),(0,d)]
 else:v=[(0,0),(w,0),(w,d),(.72*w,d),(.72*w,.35*d),(.28*w,.35*d),(.28*w,d),(0,d)]
 p=Polygon(v);p=translate(p,xoff=-p.centroid.x,yoff=-p.centroid.y);yaw=float(rng.uniform(0,360));p=translate(rotate(p,yaw,origin=(0,0)),xoff=24,yoff=24)
 return dict(type=kind,yaw=rounded(yaw),height=rounded(rng.uniform(4,7)),polygon=[[rounded(x),rounded(y)] for x,y in list(p.exterior.coords)[:-1]],thermal_thickness_m=.02),p
rows=[]
for btype in BUILDINGS:
 for count in [1,2,3]:
  splits=np.array(['train']*16+['validation']*4+['test']*4);rng.shuffle(splits)
  for j in range(24):
   b,p=building(btype);ts=[]
   for k in range(count):
    t=tree()
    for attempt in range(10000):
     if k==0 or rng.random()<.35:
      x,y=rng.uniform(7,41,2)
     else:
      a=ts[int(rng.integers(k))];theta=rng.uniform(0,2*math.pi);dist=a['radius']+t['radius']+rng.uniform(.5,7)
      x=a['x']+dist*math.cos(theta);y=a['y']+dist*math.sin(theta)
     x,y=rounded(x),rounded(y);point=Point(x,y);gap=p.distance(point)-t['radius']
     gaps=[math.hypot(x-a['x'],y-a['y'])-t['radius']-a['radius'] for a in ts]
     if not p.covers(point) and gap>=.5 and all(g>=.5 for g in gaps) and min(x,y,48-x,48-y)>=t['radius']+4 and (gap<=7 if not ts else min([gap]+gaps)<=7):break
    else:raise RuntimeError('placement failure')
    t.update(id=f'v{k}',x=x,y=y,building_gap_m=rounded(gap));ts.append(t)
   ignited=rng.choice(count,size=1 if count==1 or rng.random()<.75 else 2,replace=False).tolist()
   for k,t in enumerate(ts):t['initialized']=k in ignited
   rows.append(dict(id=f'S{len(rows)+1:03d}',kind='scene',split=str(splits[j]),building=b,trees=ts,wind_speed=rounded(rng.uniform(.5,8)),wind_from_deg=rounded(rng.uniform(0,360)),fds_seed=int(rng.integers(1,10000000)),stratum=f'{btype}_{count}'))
for kind in range(3):
 splits=np.array(['train']*16+['validation']*4+['test']*4);rng.shuffle(splits)
 for j in range(24):
  t=tree(kind);t.update(id='v0',x=24.,y=24.,initialized=True)
  rows.append(dict(id=f'C{kind*24+j+1:03d}',kind='component',split=str(splits[j]),building=None,trees=[t],wind_speed=rounded(rng.uniform(.5,8)),wind_from_deg=rounded(rng.uniform(0,360)),fds_seed=int(rng.integers(1,10000000)),stratum=f'single_{TYPES[kind]["id"]}'))
# Display ordering is randomized independently of train/test membership.
order=rng.permutation(len(rows));rows=[rows[i] for i in order]
for c in rows:
 c['domain_m']=[0,48,0,48,0,24];c['horizon_s']=180;c['provisional_cell_m']=.5
 c['initialization']=dict(type='artificial_contact_particles',duration_s=20,removed_by_s=21,temperature_C=1500,policy='Nominal ring at lower crown; strength calibration pending, common rule for all splits.')
 c['ground']=dict(type='bare_thermally_responsive',combustible=False,measure=['surface_temperature','incident_radiation','convective_flux'],material='Generic ground thermal properties to be fixed before decks; identical definition in every split.')
 c['status']='INPUT_ONLY_NOT_SIMULATED';c['label']=None
lib=dict(canopies=TYPES,buildings=[dict(id=t,height_m=[4,7],extent_m=[8,12],flat_roof=True,solid_extrusion=True) for t in BUILDINGS],node_definition=dict(vegetation='Whole crown; identical state definition and shared rule for every type.',building='Approximately1m2 surface patches on all exposed walls and roofs; orientations retained.'),materials='Generic vegetation with four disjoint particle fuel classes; generic20mm wood thermal surface; not calibrated species/roof assemblies.')
manifest=dict(seed=SEED,status='REVIEW_INPUTS_ONLY',case_count=len(rows),library=lib,cases=rows,split_policy='Random assignment within building-form × canopy-count strata and standalone-type strata;16/4/4 per24. Same conditional generator for every split; no outcomes used. Stratified random design, not claim of strictly independent unstratified draws.',training_policy='All candidate models receive the identical192 training case IDs. Same48 validation and48 test IDs. Additive model must be fit under additive constraints on the same training pool; single-only variant is separately labelled. No FDS truth supplied during autonomous training rollouts. No splitting time rows, nodes, or replicates across splits.',evaluation='Primary test: unseen draws of same scene-size and component distributions. No larger-composition generalization claim. Freeze models and predictions before new test outcomes. Building criterion:any part reaching350C; check complete boundary evidence. Report all outcomes including source ignition failures; no deleting hard negatives.',primary_target='Time-varying3D gas temperature and HRRPUV; vegetation temperature/fuel; ground and building temperatures and heat fluxes. Ignition secondary.',ground_policy='Bare ground; measure heating. User selected no combustible ground cover in this first dataset.',no_runs=True)
(OUT/'catalogue.json').write_text(json.dumps(manifest,indent=2))
# Exact unique configuration and non-intersection checks.
keys=[]
for c in rows:
 t=c['trees'];assert len({q['id'] for q in t})==len(t)
 if c['building']:
  p=Polygon(c['building']['polygon']);assert p.is_valid
  for q in t:assert not p.intersects(Point(q['x'],q['y']).buffer(q['radius']+.49))
 for i,q in enumerate(t):
  for a in t[i+1:]:assert math.hypot(q['x']-a['x'],q['y']-a['y'])>=q['radius']+a['radius']+.49
 keys.append(hashlib.sha256(json.dumps([c['building'],t,c['wind_speed'],c['wind_from_deg']],sort_keys=True).encode()).hexdigest())
assert len(set(keys))==288
report=dict(counts=dict(collections.Counter(c['split'] for c in rows)),by_kind={k:dict(collections.Counter(c['split'] for c in rows if c['kind']==k)) for k in ['scene','component']},unique_configurations=len(keys),all_geometry_clearances_pass=True,split_details={})
for split in ['train','validation','test']:
 cs=[c for c in rows if c['split']==split];report['split_details'][split]=dict(building_types=dict(collections.Counter(c['building']['type'] for c in cs if c['building'])),canopy_types=dict(collections.Counter(t['type'] for c in cs for t in c['trees'])),wind_sectors=dict(collections.Counter(int(c['wind_from_deg']//45) for c in cs)),speed_range=[min(c['wind_speed'] for c in cs),max(c['wind_speed'] for c in cs)],moisture_range=[min(t['moisture'] for c in cs for t in c['trees']),max(t['moisture'] for c in cs for t in c['trees'])])
 assert len(report['split_details'][split]['wind_sectors'])==8
(OUT/'input-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

(OUT/'splits.json').write_text(json.dumps({split:sorted(c['id'] for c in rows if c['split']==split) for split in ['train','validation','test']},indent=2))
