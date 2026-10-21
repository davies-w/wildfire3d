"""Predeclared small factorial: height x loading x forcing. Frozen instances."""
from pathlib import Path
import json,copy,hashlib,random
import legacy_single as old
R=Path(__file__).parent

def main():
 assert not (R/'budget.json').exists();base=json.loads((R/'data/original-template.json').read_text());cases=[];templates={};hashes={};expected={}
 combos=[(h,l,p) for h in [6.,8.,10.] for l in [.8,1.2] for p in [0,1]]
 # Fixed shuffled assignment; each height/loading/forcing appears in training.
 splits=['train']*12
 for i in [1,8]:splits[i]='validation'
 for i in [4,11]:splits[i]='test'
 for i,((height,loading,profile),split) in enumerate(zip(combos,splits)):
  ts=copy.deepcopy(base);ts['A']['model']['height']=height
  for p in ts['A']['particles']:p['xyz'][2]=round(2+(p['xyz'][2]-2)*height/8,8);p['weight']*=height/8*loading
  old.old.MODELS['A']['height']=height
  w,angle=[(1.8,240.),(3.8,300.)][profile];name=f'v31_{i:02d}'
  c=dict(case=name,split=split,family='single',trees=[dict(type='A',x=8.,y=8.)],heater_type='A',heater_xy=[8.,8.],strength=1.,duration=20,wind_speed=w,angle_deg=angle,horizon_s=180,variant='passive',profile=False,solve_limit_s=1200,dx=.5,crown_height_m=height,loading_multiplier=loading,forcing_profile=profile)
  s,e=old.deck(c,ts);c['deck_sha256']=hashlib.sha256(s.encode()).hexdigest();(R/'decks'/(name+'.fds')).write_text(s);cases.append(c);templates[name]=ts;expected[name]=e;hashes[name]=c['deck_sha256']
 (R/'cases.json').write_text(json.dumps(cases,indent=2));(R/'data/tree-templates.json').write_text(json.dumps(templates));(R/'data/expected-particles.json').write_text(json.dumps(expected));(R/'results/input-freeze.json').write_text(json.dumps(dict(cases=hashes,template_sha256=hashlib.sha256((R/'data/tree-templates.json').read_bytes()).hexdigest(),rule='Transform original frozen z coordinates, height/8 times loading particle weight; no resampling. Eight train/two validation/two fresh test; tests not launched before model/prediction freeze.'),indent=2));print('Prepared 12 cases; 8 train, 2 validation, 2 untouched test')
if __name__=='__main__':main()
