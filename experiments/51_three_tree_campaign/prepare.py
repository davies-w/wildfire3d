"""Freeze the revised 2,000-case design without launching or changing old experiments."""
from pathlib import Path
import collections, gzip, hashlib, itertools, json, random
R=Path(__file__).resolve().parent
D=R/'data'; D.mkdir(exist_ok=True)
rng=random.Random(5102026)
def read(p): return json.loads(p.read_text())
def rows(p):
 with gzip.open(p,'rt') as f: return [json.loads(x) for x in f]
def signature(c): return tuple(c[k] for k in ('geometry_id','ignition_index','wind_m_s','moisture_fraction','loading_multiplier'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
old=R.parent/'48_two_tree_design'; compact=R.parent/'49_compact_tree_domain'; oak=R.parent/'50_live_oak'
geoms=read(old/'data/geometries.json')+[g for g in read(oak/'data/geometries.json') if g['crown_radius_m'] in [6,7] and g['total_height_m'] in [10,11]]
G={g['id']:g for g in geoms}; assert len(G)==54
prior=read(compact/'data/cases.json')+read(oak/'data/pilot/cases.json')
reuse={}
for c in prior:
 if c['variant']!='baseline' or c['geometry_id'] not in G: continue
 folder=(compact if c['type_id']!=2 else oak)/'data/completed'/c['pilot_case']
 proof=folder/'proof.json'; assert proof.exists()
 reuse[signature(c)]=dict(case=c['pilot_case'],proof_path=str(proof.relative_to(R.parents[1])),proof_sha256=digest(proof),deck_sha256=c['deck_sha256'])
selected=[]
for typ,target in [(1,667),(3,667),(2,666)]:
 gs=[g for g in geoms if g['type_id']==typ]; gs.sort(key=lambda g:g['id'])
 pool=rows(old/'data/cases.jsonl.gz') if typ!=2 else rows(oak/'data/cases.jsonl.gz')
 for i,g in enumerate(gs):
  n=target//len(gs)+(i<target%len(gs))
  for family in [0,1]:
   take=n//2+(n%2 and family==i%2)
   available=[c for c in pool if c['geometry_id']==g['id'] and c['ignition_index']//24==family]
   must=[c for c in available if signature(c) in reuse]
   if typ==2:
    available=[dict(geometry_id=g['id'],type_id=2,ignition_index=j,wind_m_s=w,moisture_fraction=m,loading_multiplier=l) for j,w,m,l in itertools.product(range(family*24,(family+1)*24),range(1,6),[.06,.12,.18,.24,.30],[.7,1.,1.3])]
   rng.shuffle(available)
   chosen=list(must); seen={signature(c) for c in chosen}
   # Greedy marginal balance, without selecting on simulation outcomes.
   keys=['wind_m_s','moisture_fraction','loading_multiplier','ignition_index']
   while len(chosen)<take:
    counts={k:collections.Counter(c[k] for c in chosen) for k in keys}
    candidates=[c for c in available if signature(c) not in seen]
    c=min(candidates,key=lambda c:sum(counts[k][c[k]] for k in keys))
    chosen.append(c);seen.add(signature(c))
   for c in chosen:
    index=len(selected); name=f'tree51_{index:06d}'
    c=dict(c); source=c.pop('case',None); c.update(case=name,source_design_case=source,seed=c.get('seed',5100000+index),domain=[29,20,max(16,g['total_height_m']+6)] if typ==2 else [24,16,g['total_height_m']+6],dx=.5,horizon_s=180,checkpoint_initial_seconds=480)
    c['reuse']=reuse.get(signature(c)); selected.append(c)
assert len(selected)==2000 and len({signature(c) for c in selected})==2000
assert collections.Counter(c['type_id'] for c in selected)=={1:667,3:667,2:666}
assert sum(c['reuse'] is not None for c in selected)==22
# Environment groups stay in one split across geometries and ignition locations.
environments=list(itertools.product(range(1,6),[.06,.12,.18,.24,.30]));rng.shuffle(environments)
split={x:('train' if i<18 else 'validation' if i<22 else 'test') for i,x in enumerate(environments)}
for c in selected:c['split']=split[(c['wind_m_s'],c['moisture_fraction'])]
with (D/'cases.jsonl.gz').open('wb') as raw:
 with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as f:
  for c in selected:f.write((json.dumps(c,sort_keys=True)+'\n').encode())
(D/'geometries.json').write_text(json.dumps(geoms,indent=2)+'\n')
summary=dict(cases=2000,counts_by_type=dict(collections.Counter(c['type_id'] for c in selected)),oak_width_height_m=[[2*g['crown_radius_m'],g['total_height_m']] for g in gs],reused_completed_cases=22,new_cases=1978,counts_by_split=dict(collections.Counter(c['split'] for c in selected)),cases_sha256=digest(D/'cases.jsonl.gz'),limitations='Design only. Historical pilot outcomes have been inspected: held-out environments are grouped but not historically pristine. Species-inspired shapes and generic fuel chemistry; no embers, bark or grass. Imposed0.4m1500C20s patch,0.5m mesh,180s target; no oak height controls.')
(D/'design.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
