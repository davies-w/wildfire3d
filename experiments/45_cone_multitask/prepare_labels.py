"""Reuse verified train cones; extract frozen held-out labels without model fitting."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
R=Path(__file__).resolve().parent;E=R.parent;repo=E.parent;D=R/'data';D.mkdir(exist_ok=True)
sys.path.insert(0,str(E/'44_hot_gas_cones'))
from extract_training import source_frames,frame,code_hash
schema=json.loads((E/'36_tree_density/learning-schema.json').read_text());rot=schema['rotations'][0]
old={x['conditions']['case']:x for x in json.loads((E/'35_surrogate_diagnostics/attempt12/inventory.json').read_text())};new={x['case']:x for x in json.loads((E/'36_tree_density/cases.json').read_text())}
with np.load(E/'36_tree_density/data/learning/sequences.npz') as a:times=a['time']
trainplan=json.loads((E/'44_hot_gas_cones/data/training-plan.json').read_text());train={x['case_index']:x for x in trainplan['cases']}
keys=['pivot_height_m','tilt_from_vertical_deg','length_m','end_radius_m','peak_temperature_C'];params=np.zeros((2080,91,5),np.float32);active=np.zeros((2080,91),bool);sources=[]
held=D/'heldout-cones';held.mkdir(exist_ok=True)
for split in ['train','validation','test']:
 for idx in rot[split]:
  c=schema['cases'][idx];name=c['case'];key=c['physical_key']
  if split=='train':
   item=train[idx];p=E/'44_hot_gas_cones/data/training-histories'/f'{name}.json';r=json.loads(p.read_text());assert r['recipe_sha256']==code_hash() and r['source_sha256']==item['sha256']
  else:
   if c['source']=='density36':
    folder=E/'36_tree_density/data/verified-material'/name;proof=json.loads((folder/'verified.json').read_text());sf=[n for n in proof['retained_material_inputs'] if n.endswith('.sf')];assert len(sf)==1
    source=folder/sf[0];expected=proof['members'][sf[0]]['sha256'];kind='verified_temperature_slice';conditions=new[name]
   else:
    it=old[name];source=E/it['archive'];conditions=it['conditions'];proof=json.loads((E/'35_surrogate_diagnostics/attempt12/data/states'/f'{name}.json').read_text());expected=proof['raw_sha256'];kind='verified_local_archive'
   item=dict(case=name,path=source.relative_to(repo).as_posix(),sha256=expected,source_kind=kind,origin_m=[-4,-4,0] if conditions.get('expanded') else [0,0,0])
   p=held/f'{name}.json'
   if p.exists():
    r=json.loads(p.read_text());assert r['recipe_sha256']==code_hash() and r['source_sha256']==expected
   else:
    rows=[frame(temp,float(key[0]),t) for t,temp in source_frames(item)]
    r=dict(case=name,case_index=idx,split=split,source_sha256=expected,recipe_sha256=code_hash(),snapshots=rows);p.write_text(json.dumps(r,separators=(',',':'),allow_nan=False)+'\n')
  assert len(r['snapshots'])==91 and np.allclose([x['time_s'] for x in r['snapshots']],times[idx],atol=1e-5,rtol=0)
  for j,row in enumerate(r['snapshots']):
   active[idx,j]=row['active']
   if row['active']:params[idx,j]=[row['cone'][k] for k in keys];assert row['cone_metrics']['hot_recall']>=.95-1e-9
  sources.append(dict(case=name,case_index=idx,split=split,source_path=item['path'],source_sha256=item['sha256'],label_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
  if len(sources)%20==0:print('Verified cone labels',len(sources),'/2080',flush=True)
assert len(sources)==2080 and len({x['case_index'] for x in sources})==2080
out=D/'labels';out.mkdir(exist_ok=True);np.savez_compressed(out/'cones.npz',parameters=params,active=active,time=times,case_indices=np.arange(2080))
(out/'schema.json').write_text(json.dumps(dict(keys=keys,scales=[12.,90.,24.,16.,1500.],scale_policy='Fixed physical unit scales, no validation or test fitting',inactive='Zero placeholders; regression masked by reference active flag',recipe_sha256=code_hash(),split_counts={k:len(rot[k]) for k in ['train','validation','test']},source_records=sources),indent=2)+'\n')
print('All labels complete; test labels extracted only, no predictions or test scores evaluated',flush=True)
