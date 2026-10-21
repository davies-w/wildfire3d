"""Prepare balanced discrete configurations and grouped seed repeats. No cloud calls."""
from pathlib import Path
import itertools,json,copy,hashlib,re
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import lil_matrix
import legacy_single as engine
R=Path(__file__).parent
LEVELS={'crown_height_m':[4.,6.,8.,10.],'moisture':[.06,.12,.18,.24,.30],'loading_multiplier':[.7,1.,1.3],'wind_speed':[1.,3.,5.],'angle_deg':[0.,90.,180.]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def assign(pool,counts,seed):
 n=len(pool);splits=list(counts);constraints=[];lo=[];hi=[]
 for i in range(n):constraints.append([j*n+i for j in range(len(splits))]);lo.append(0);hi.append(1)
 for j,s in enumerate(splits):
  constraints.append(list(range(j*n,(j+1)*n)));lo.append(counts[s]);hi.append(counts[s])
  for k,levels in LEVELS.items():
   for v in levels:
    constraints.append([j*n+i for i,c in enumerate(pool) if c[k]==v]);lo.append(counts[s]//len(levels));hi.append(int(np.ceil(counts[s]/len(levels))))
 A=lil_matrix((len(constraints),n*len(splits)))
 for i,cols in enumerate(constraints):A[i,cols]=1
 ans=milp(np.random.default_rng(seed).uniform(0,1,n*len(splits)),integrality=np.ones(n*len(splits)),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),lo,hi),options={'time_limit':40,'mip_rel_gap':.1})
 assert ans.x is not None,ans.message
 x=np.rint(ans.x).astype(int);assert np.all(A@x>=np.array(lo)-1e-6) and np.all(A@x<=np.array(hi)+1e-6)
 return {s:[pool[i] for i in range(n) if x[j*n+i]] for j,s in enumerate(splits)}
def main():
 assert not (R/'budget.json').exists();(R/'data/decks').mkdir(exist_ok=True)
 pool=[dict(zip(LEVELS,v)) for v in itertools.product(*LEVELS.values())];parts=assign(pool,{'train':360,'validation':32,'test':40},3201)
 base=json.loads((R/'data/original-template.json').read_text());templates={};geomhash={}
 for h,l in itertools.product(LEVELS['crown_height_m'],LEVELS['loading_multiplier']):
  key=f'h{h:g}_l{l:g}';t=copy.deepcopy(base);t['A']['model']['height']=h
  for p in t['A']['particles']:p['xyz'][2]=round(2+(p['xyz'][2]-2)*h/8,8);p['weight']*=h/8*l
  templates[key]=t;geomhash[key]=hashlib.sha256(json.dumps(t,sort_keys=True).encode()).hexdigest()
 configs=[]
 for split,rows in parts.items():
  for c in rows:configs.append(dict(c,split=split,configuration=f'x32_{len(configs):03d}',geometry_key=f"h{c['crown_height_m']:g}_l{c['loading_multiplier']:g}"))
 # Choose20 representative configurations, balanced globally across height/moisture,
 # with12train/4validation/4test; all replicas stay in the original split.
 n=len(configs);con=[];low=[];high=[]
 for split,count in [('train',12),('validation',4),('test',4)]:con.append([i for i,c in enumerate(configs) if c['split']==split]);low.append(count);high.append(count)
 for k,levels in LEVELS.items():
  for v in levels:con.append([i for i,c in enumerate(configs) if c[k]==v]);low.append(20//len(levels));high.append(int(np.ceil(20/len(levels))))
 A=lil_matrix((len(con),n))
 for i,ids in enumerate(con):A[i,ids]=1
 z=milp(np.random.default_rng(3202).uniform(size=n),integrality=np.ones(n),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),low,high),options={'time_limit':20});assert z.x is not None;repeat=set(np.flatnonzero(z.x>.5));assert len(repeat)==20
 rng=np.random.default_rng(3203);seeds=rng.choice(1_000_000,size=472,replace=False)+10_000;cases=[]
 for i,c in enumerate(configs):
  for replica in range(3 if i in repeat else 1):
   name=c['configuration']+f'_s{replica}';key=c['geometry_key'];seed=int(seeds[len(cases)]);engine.old.MODELS['A']['height']=c['crown_height_m']
   row=dict(c,case=name,seed=seed,replica=replica,family='single',trees=[dict(type='A',x=8.,y=8.)],heater_type='A',heater_xy=[8.,8.],strength=1.,duration=20,horizon_s=180,variant='passive',profile=False,solve_limit_s=1200,dx=.5)
   deck,_=engine.deck(row,templates[key]);deck,nm=re.subn(r'MOISTURE_CONTENT\s*=\s*[0-9.]+',f"MOISTURE_CONTENT={c['moisture']}",deck);assert nm==4;deck,ns=re.subn(r'RND_SEED\s*=\s*\d+',f'RND_SEED={seed}',deck);assert ns==1
   path=R/'data/decks'/(name+'.fds');path.write_text(deck);row.update(deck_sha256=sha(path),geometry_sha256=geomhash[key]);cases.append(row)
 old=json.loads((R.parent/'31_tree_variations/development.json').read_text());reuse=[dict(case=c['case'],split=c['split'],source_experiment='31_tree_variations' if c['new_geometry'] else '27_single_tree_cnn',seed=4321,moisture=.12) for c in old]
 assert len(reuse)==48 and len(cases)==472
 for config in configs:assert len({r['split'] for r in cases if r['configuration']==config['configuration']})==1
 save(R/'cases.json',cases);save(R/'configurations.json',configs);save(R/'reuse.json',reuse);save(R/'data/tree-templates.json',templates)
 coverage={s:{k:{str(v):sum(c[k]==v for c in configs if c['split']==s) for v in values} for k,values in LEVELS.items()} for s in parts}
 save(R/'results/design.json',dict(levels=LEVELS,unique_new=432,new_FDS_runs=472,reused_runs=48,total_unique=480,total_trajectories=520,new_by_split={s:sum(c['split']==s for c in cases) for s in parts},total_unique_by_split={'train':400,'validation':40,'test':40},total_trajectories_by_split={'train':424,'validation':48,'test':48},seed_repeat_configurations=[configs[i]['configuration'] for i in sorted(repeat)],coverage=coverage,seed_is_model_input=False,split_group='complete physical configuration including every seed replica',status='prepared_not_launched'))
 save(R/'results/input-freeze.json',dict(template_sha256=sha(R/'data/tree-templates.json'),source_template_sha256=sha(R/'data/original-template.json'),cases={c['case']:c['deck_sha256'] for c in cases},manifest_sha256=sha(R/'cases.json')))
 print('Prepared472new decks:432unique configurations +40extra seed replicas;48existing trajectories reused.')
if __name__=='__main__':main()
