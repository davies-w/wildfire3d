"""Generate exactly the requested in-range density additions; never solve locally."""
from pathlib import Path
import itertools,json,hashlib,re,copy
import numpy as np
import legacy_single as engine
R=Path(__file__).resolve().parent;old=R.parent/'32_tree_expansion'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert not (R/'results/reserved.json').exists(),'Frozen campaign cannot be regenerated'
 (R/'data/decks').mkdir(exist_ok=True);ts=json.loads((R/'data/tree-templates.json').read_text());prior=json.loads((old/'cases.json').read_text());keys=['crown_height_m','moisture','loading_multiplier','wind_speed','angle_deg'];existing={tuple(c[k] for k in keys) for c in prior}
 pool=[]
 for h,m,l,w,ang in itertools.product([4.,6.,8.,10.],[.06,.12,.18,.24,.30],[.7,1.,1.3],[1.,2.,3.,4.,5.],[0.,45.,90.,135.,180.,225.,315.]):
  if w in [2.,4.] or ang in [45.,135.,225.,315.]:pool.append(dict(zip(keys,[h,m,l,w,ang])))
 assert len(pool)==1560 and all(tuple(c[k] for k in keys) not in existing for c in pool)
 rng=np.random.default_rng(3601);used={c['seed'] for c in prior};seeds=[]
 while len(seeds)<len(pool):
  n=int(rng.integers(2000000,2000000000))
  if n not in used:seeds.append(n);used.add(n)
 cases=[]
 for i,c in enumerate(pool):
  name=f'x36_{i:04d}_s0';key=f"h{c['crown_height_m']:g}_l{c['loading_multiplier']:g}";engine.old.MODELS['A']['height']=c['crown_height_m']
  row=dict(c,case=name,configuration=f'x36_{i:04d}',geometry_key=key,seed=seeds[i],replica=0,split='pool',family='single',trees=[dict(type='A',x=8.,y=8.)],heater_type='A',heater_xy=[8.,8.],strength=1.,duration=20,horizon_s=180,variant='passive',profile=False,solve_limit_s=1200,dx=.5)
  deck,_=engine.deck(row,ts[key]);deck,n=re.subn(r'MOISTURE_CONTENT\s*=\s*[0-9.]+',f"MOISTURE_CONTENT={c['moisture']}",deck);assert n==4;deck,n=re.subn(r'RND_SEED\s*=\s*\d+',f'RND_SEED={seeds[i]}',deck);assert n==1
  p=R/'data/decks'/(name+'.fds');p.write_text(deck);row.update(deck_sha256=sha(p),geometry_sha256=hashlib.sha256(json.dumps(ts[key],sort_keys=True).encode()).hexdigest());cases.append(row)
 # Coverage spanning extremes, all four diagonals and both new wind speeds.
 wanted=[(4.,.06,.7,2.,45.),(10.,.3,1.3,4.,225.),(4.,.3,1.3,5.,135.),(10.,.06,.7,1.,315.),(6.,.18,1.,2.,0.),(8.,.24,1.,4.,180.)]
 coverage=[next(c['case'] for c in cases if tuple(c[k] for k in keys)==v) for v in wanted]
 # Expected initial-density arrays reused only for identical geometry and moisture.
 geoms=np.load(old/'data/geometries.npz');expected={}
 for name in coverage:
  c=next(c for c in cases if c['case']==name);ref=next(q for q in prior if all(q[k]==c[k] for k in keys[:3]) and q['case'] in geoms.files);expected[name]=geoms[ref['case']]
 np.savez_compressed(R/'data/coverage-geometries.npz',**expected)
 save(R/'cases.json',cases);save(R/'results/design.json',dict(new_runs=1560,new_configurations=1560,existing_histories=520,total_histories=2080,total_configurations=2040,coverage_cases=coverage,angles=[0,45,90,135,180,225,315],winds=[1,2,3,4,5],missing_existing_grid_cells_not_added=108,south270_not_added=True))
 save(R/'results/input-freeze.json',dict(template_sha256=sha(R/'data/tree-templates.json'),cases={c['case']:c['deck_sha256'] for c in cases},manifest_sha256=sha(R/'cases.json')))
 # Rebuild an old deck to prove the generator itself has not changed the science.
 c=prior[0];engine.old.MODELS['A']['height']=c['crown_height_m'];deck,_=engine.deck(c,ts[c['geometry_key']]);deck=re.sub(r'MOISTURE_CONTENT\s*=\s*[0-9.]+',f"MOISTURE_CONTENT={c['moisture']}",deck);deck=re.sub(r'RND_SEED\s*=\s*\d+',f"RND_SEED={c['seed']}",deck);assert hashlib.sha256(deck.encode()).hexdigest()==c['deck_sha256']
 for c in cases:
  deck=(R/'data/decks'/(c['case']+'.fds')).read_text();assert 'DT_RESTART=30.' in deck and 'IJK=48,32,32' in deck and 'T_END=180' in deck
 save(R/'results/preflight.json',dict(passed=True,no_local_solves=True,new_decks=1560,old_deck_exact_reconstruction=True,no_existing_configuration_duplicates=True,cloud_resume_required_every_case=True,coverage_required_before_bulk=True));print('Prepared1560decks; old deck reconstruction exact')
if __name__=='__main__':main()
