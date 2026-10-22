import json,random,math,collections
from pathlib import Path
ROOT=Path(__file__).parent;rng=random.Random(241018)
models=[dict(id='N',name='Narrow cone',r=1.5,base=2,height=8,shape='cone'),dict(id='B',name='Broad cone',r=2.5,base=2,height=5,shape='cone'),dict(id='C',name='Column',r=1.5,base=2,height=8,shape='cylinder'),dict(id='S',name='Small cone',r=1.5,base=1,height=4,shape='cone')]
def pack(counts):
 bx=rng.randrange(6,23)/2;by=rng.randrange(6,23)/2;building=[bx,by,6,6,5];trees=[]
 types=[m for m,c in zip(models,counts) for _ in range(c)];rng.shuffle(types);types.sort(key=lambda m:-m['r'])
 for m in types:
  for attempt in range(1500):
   x=round(rng.uniform(1+m['r'],19-m['r']),2);y=round(rng.uniform(1+m['r'],19-m['r']),2)
   gap=math.hypot(max(bx-x,0,x-bx-6),max(by-y,0,y-by-6))-m['r']
   if gap<.5:continue
   if any(math.hypot(x-t['x'],y-t['y'])<m['r']+t['r']+.5 for t in trees):continue
   trees.append(dict(model=m['id'],x=x,y=y,r=m['r'],initialized=False));break
  else:return None
 if trees:rng.choice(trees)['initialized']=True
 return dict(building=building,trees=trees,counts=dict(zip([m['id'] for m in models],counts)))
scenes=[];rejected=0
while len(scenes)<64:
 counts=[rng.randrange(4) for _ in models];c=pack(counts)
 if c is None:rejected+=1;continue
 c.update(id=f'L{len(scenes)+1:02}',family='lot',split=None);scenes.append(c)
indices=list(range(64));rng.shuffle(indices)
for j,i in enumerate(indices):scenes[i]['split']='train' if j<40 else ('validation' if j<52 else 'test')
for m in models:
 # One-component configurations with the same building and environmental setup.
 ss=['train','train','validation','test'];rng.shuffle(ss)
 for j,split in enumerate(ss):
  c=None
  while c is None:c=pack([int(k['id']==m['id']) for k in models])
  c.update(id=f'{m["id"]}{j+1}',family='single',split=split);scenes.append(c)
assert len(scenes)==80
for c in scenes:
 for t in c['trees']:
  assert 0<=t['x']-t['r'] and t['x']+t['r']<=20
 for i,a in enumerate(c['trees']):
  for b in c['trees'][i+1:]:assert math.hypot(a['x']-b['x'],a['y']-b['y'])>=a['r']+b['r']+.5
obj=dict(status='INPUT_REVIEW_ONLY_NO_DECKS_OR_SIMULATIONS',seed=241018,models=models,cases=scenes,domain=[20,20,15],dx=.5,horizon=180,wind_speed=3,wind_toward='+x',moisture=.12,building='6x6x5m square solid block, variable half-metre position, axis-aligned',ground='Heatable noncombustible generic soil',source='One randomly selected canopy receives identical policy20s artificial hot-particle initialization; none if zero trees',rejected_placements=rejected)
(ROOT/'data/catalogue.json').write_text(json.dumps(obj,indent=2))
audit=dict(counts=dict(collections.Counter(c['split'] for c in scenes)),lot_tree_count_range=[min(len(c['trees']) for c in scenes[:64]),max(len(c['trees']) for c in scenes[:64])],packing_rejections=rejected,type_count_coverage={m['id']:sorted(set(c['counts'][m['id']] for c in scenes[:64])) for m in models},same_distribution='Splits assigned after geometry-only rejection, blind to outcomes; single-component family stratified by type; no shared geometry copies across splits')
(ROOT/'data/audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit))
