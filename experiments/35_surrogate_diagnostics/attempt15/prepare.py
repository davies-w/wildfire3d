"""Prepare minimal material histories locally. User approved fuel-release rate as the third state. No training."""
from pathlib import Path
import json,tarfile,csv,io,hashlib
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent/'attempt12';E=R.parents[1]
(R/'data/cases').mkdir(parents=True,exist_ok=True);(R/'results').mkdir(exist_ok=True)
items=json.loads((P/'inventory.json').read_text());prior=json.loads((R.parent/'attempt13/schema.json').read_text());states=[];times=[];conditions=[];proof=[]
def table(b):
 rows=list(csv.reader(io.StringIO(b.decode())));return rows[1],np.array(rows[2:],float)
for j,it in enumerate(items):
 n=it['conditions']['case'];p=R/'data/cases'/f'{n}.npz';c=it['conditions'];d=json.loads((P/'data/states'/f'{n}.json').read_text());audit=json.loads((R.parent/'attempt14/data'/f'{n}.json').read_text())
 if not p.exists():
  csvs={}
  with tarfile.open(E/it['archive']) as tar:
   for m in tar:
    if m.name.endswith(('_hrr.csv','_devc.csv')):csvs[Path(m.name).name]=table(tar.extractfile(m).read())
  hk,h=csvs[n+'_hrr.csv'];dk,a=csvs[n+'_devc.csv'];ht=h[:,0];at=a[:,0];target=np.array([v['time_s'] for v in d['snapshots']]);water_rate=h[:,hk.index('MLR_WATER VAPOR')];water=audit['initial_water_estimate_kg']-np.cumsum(water_rate*np.diff(ht,prepend=ht[0]));fr=a[:,[i for i,k in enumerate(dk) if k.startswith('v0 fuel')]].sum(1);consumed=np.r_[0,np.cumsum((fr[:-1]+fr[1:])*.5*np.diff(at))]/.75;dry=audit['initial_dry_estimate_kg']-consumed
  raw=np.stack([np.interp(target,ht,water),np.interp(target,at,dry),np.interp(target,at,fr)],-1)
  np.savez_compressed(p,time=target,raw_candidates=raw,initial=np.array([audit['initial_water_estimate_kg'],audit['initial_dry_estimate_kg']]))
 with np.load(p) as z:raw=z['raw_candidates'];t=z['time'];init=z['initial']
 assert raw.shape==(91,3) and np.isfinite(raw).all();states.append(raw);times.append(t);conditions.append([c.get('crown_height_m',8),c.get('loading_multiplier',1),c['wind_speed'],np.cos(np.deg2rad(c['angle_deg'])),np.sin(np.deg2rad(c['angle_deg']))]);proof.append(dict(case=n,negative_water_min_kg=float(min(0,raw[:,0].min())),negative_dry_min_kg=float(min(0,raw[:,1].min())),negative_release_min_kg_s=float(min(0,raw[:,2].min())),max_water_increase_kg=float(max(0,np.diff(raw[:,0]).max())),max_dry_increase_kg=float(max(0,np.diff(raw[:,1]).max())),raw_sha256=d['raw_sha256']))
 if j%50==0:print('PREPARED',j+1,flush=True)
old=np.load(R.parent/'attempt13/data/sequences.npz');np.savez_compressed(R/'data/candidates.npz',state=np.array(states),time=np.array(times),conditions=np.array(conditions),fold=old['fold'],configuration=old['configuration'])
meta=dict(status='approved three-state training data',candidate_state_names=['estimated_remaining_water_kg','estimated_remaining_unreacted_vegetation_kg','vegetation_fuel_release_kg_s'],conditions=['height_m','loading_multiplier','wind_x_m_s','cos_ignition_angle','sin_ignition_angle'],forcing=['known_ignition_command','actual_dt_s'],cases=prior['cases'],rotations=prior['rotations'],scope='Char treated as inert as requested. Release is pyrolysis output, not measured heat release. Full520 histories; existing grouped folds retained; not historically pristine. No plume state or exact gas/temperature output.')
(R/'schema.json').write_text(json.dumps(meta,indent=2));(R/'results/prepared.json').write_text(json.dumps(dict(histories=520,configurations=480,shape=[520,91,3],transitions=46800,per_case=proof,training=False,third_state_approved=True),indent=2));print('COMPLETE 520 histories, candidate state shape520x91x3',flush=True)
