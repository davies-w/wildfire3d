import json,random,math,collections
from pathlib import Path
ROOT=Path(__file__).parent;rng=random.Random(251018)
old=json.loads((ROOT/'source-catalogue.json').read_text());models=old['models'];lookup={m['id']:m for m in models};cases=[]
def tree(t,x,y,init=False):return dict(model=t,x=round(x,3),y=round(y,3),r=lookup[t]['r'],initialized=init)
def exposure():return dict(relative_strength=round(rng.uniform(.35,1.65),2),duration_s=round(rng.uniform(5,30),1),bearing_deg=round(rng.uniform(0,360),1))
def add(family,ts,building,split,source=None,subtype=''):
 c=dict(id=f'{family}-{1+sum(c["family"]==family for c in cases):02}',family=family,trees=ts,building=building,split=split,exposure=source,subtype=subtype,counts={m['id']:sum(t['model']==m['id'] for t in ts) for m in models});cases.append(c)
for m in models:
 splits=['train']*4+['validation','test'];rng.shuffle(splits)
 for split in splits:add('isolated',[tree(m['id'],10,10)],None,split,exposure(),'one tree; controlled exposure')
for kind in ['building','ground']:
 splits=['train','train','validation','test'];rng.shuffle(splits)
 for split in splits:add('surfaces',[],[7,7,6,6,5] if kind=='building' else None,split,exposure(),kind+' heat-response control')
# Cover all16 ordered source/receiver model combinations in fitting; independent positions in each draw.
extra=['train']*8+['validation']*4+['test']*4;rng.shuffle(extra)
for i,a in enumerate(models):
 for j,b in enumerate(models):
  for split in ['train',extra[i*4+j]]:
   gap=rng.uniform(.5,3.5);dist=a['r']+b['r']+gap;angle=rng.uniform(0,2*math.pi)
   dx,dy=dist*math.cos(angle)/2,dist*math.sin(angle)/2
   add('pairs',[tree(a['id'],10-dx,10-dy,True),tree(b['id'],10+dx,10+dy)],None,split,None,'tree → tree')
def packed(types,building_present):
 for attempt in range(2000):
  b=[rng.randrange(8,21)/2,rng.randrange(8,21)/2,6,6,5] if building_present else None;ts=[]
  for typ in types:
   r=lookup[typ]['r']
   for _ in range(500):
    x=rng.uniform(1+r,19-r);y=rng.uniform(1+r,19-r)
    if b and math.hypot(max(b[0]-x,0,x-b[0]-6),max(b[1]-y,0,y-b[1]-6))<r+.5:continue
    if any(math.hypot(x-t['x'],y-t['y'])<r+t['r']+.5 for t in ts):continue
    neighbours=[math.hypot(x-t['x'],y-t['y'])-r-t['r'] for t in ts]
    if b:neighbours.append(math.hypot(max(b[0]-x,0,x-b[0]-6),max(b[1]-y,0,y-b[1]-6))-r)
    if neighbours and min(neighbours)>3.5:continue
    ts.append(tree(typ,x,y));break
   else:break
  if len(ts)==len(types):
   ts[0]['initialized']=True;return ts,b
 raise RuntimeError('cannot pack')
for m in models:
 splits=['train','train','validation','test'];rng.shuffle(splits)
 for split in splits:
  ts,b=packed([m['id']],True);add('treewall',ts,b,split,None,'tree + square building')
for withbuilding in [False,True]:
 splits=['train']*4+['validation']*2+['test']*2;rng.shuffle(splits)
 for k,split in enumerate(splits):
  types=[models[k%4]['id']]+[rng.choice(models)['id'] for _ in range(1 if withbuilding else 2)]
  ts,b=packed(types,withbuilding)
  # Include combined sources without baking a source-count shortcut into geometry.
  if k%2==1:ts[1]['initialized']=True
  add('groups',ts,b,split,None,'two trees + building' if withbuilding else 'three trees')
# Larger layouts share one input distribution across train/validation/test.
large=[c for c in old['cases'] if c['family']=='lot' and 4<=len(c['trees'])<=9];rng.shuffle(large)
large_splits=['train']*6+['validation']*3+['test']*3
rng.shuffle(large_splits)
for c,split in zip(large[:12],large_splits):add('composition',c['trees'],c['building'],split,None,'larger lot; same-family split')
for c in cases:
 for t in c['trees']:
  assert t['x']-t['r']>=.5 and t['x']+t['r']<=19.5 and t['y']-t['r']>=.5 and t['y']+t['r']<=19.5
  if c['building']:
   b=c['building'];assert math.hypot(max(b[0]-t['x'],0,t['x']-b[0]-6),max(b[1]-t['y'],0,t['y']-b[1]-6))>=t['r']+.499
 for i,a in enumerate(c['trees']):
  for b in c['trees'][i+1:]:assert math.hypot(a['x']-b['x'],a['y']-b['y'])>=a['r']+b['r']+.498
 if c['family']=='isolated':assert c['building'] is None and len(c['trees'])==1
 if c['family']=='pairs':assert c['building'] is None and len(c['trees'])==2
obj=dict(status='REVIEW_ONLY_NO_DECKS_NO_RUNS',models=models,cases=cases,seed=251018,domain=[20,20,15],dx=.5,horizon=180,wind_speed=3,wind_toward='+x',moisture=.12)
(ROOT/'data/catalogue.json').write_text(json.dumps(obj,indent=2))
audit=dict(total=len(cases),by_family=dict(collections.Counter(c['family'] for c in cases)),by_split=dict(collections.Counter(c['split'] for c in cases)),no_buildings_in_isolated=True,ordered_pair_training_coverage=len(set(tuple(t['model'] for t in c['trees']) for c in cases if c['family']=='pairs' and c['split']=='train')),notes='Whole configurations held out; artificial exposures sampled continuously and split independently per component type. Pair type coverage is stratified; not all pair type combinations occur in each small holdout. Larger layouts randomly split 6/3/3 from the same geometry-only pool; not size extrapolation. Small split counts do not guarantee coverage of every tree count or combination.')
(ROOT/'data/audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit))
