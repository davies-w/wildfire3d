"""Explicit, hashed particle instances and a predeclared type-transfer split."""
import hashlib,json,math,re
from pathlib import Path
ROOT=Path(__file__).parent
CLASSES=['foliage','small roundwood','medium roundwood','large roundwood']
MODELS={'A':dict(shape='cone',r=1.5,base=2.,height=8.),'B':dict(shape='cone',r=2.5,base=2.,height=5.),'C':dict(shape='cylinder',r=1.5,base=2.,height=8.)}
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def templates():
 old=json.loads((ROOT/'reference-particles.json').read_text());out={}
 for key,m in MODELS.items():
  volume=math.pi*m['r']**2*m['height']/(3 if m['shape']=='cone' else 1)
  ratio=volume/(math.pi*2**2*8/3);pts=[]
  for fuel in CLASSES:
   for i,p in enumerate(old[fuel][:400]):
    x,y,z=p['xyz'];u=(z-2)/8;xn=(x-5)/2;yn=(y-6)/2
    if m['shape']=='cylinder':xn/=1-u;yn/=1-u;u=1-(1-u)**3
    xyz=[round(xn*m['r'],8),round(yn*m['r'],8),round(m['base']+u*m['height'],8)]
    pts.append(dict(id=f'{fuel}-{i}',fuel=fuel,xyz=xyz,weight=p['weight']*ratio))
  # Fixed hot-particle rings; strength varies weights, never sample positions.
  heater=[dict(xyz=[round(.8*m['r']*math.cos(2*math.pi*i/1600),8),round(.8*m['r']*math.sin(2*math.pi*i/1600),8),2.1],weight=1.) for i in range(1600)]
  out[key]=dict(model=m,particles=pts,heater=heater,reference_volume_ratio=ratio)
 return out

def manifest():
 rows=[]
 profiles=[(.6,10,'train'),(1.,20,'train'),(1.4,25,'train'),(.8,25,'train'),(1.2,15,'validation'),(.7,18,'validation')]
 for typ in MODELS:
  for i,(strength,duration,split) in enumerate(profiles):rows.append(dict(case=f't26_single_{typ}_{i}',family='single',split=split,trees=[dict(type=typ,x=10.,y=10.)],heater_type=typ,heater_xy=[10.,10.],strength=strength,duration=duration))
 pairs=[('AA','train',1.3,-22),('AB','train',2.,5),('BB','train',2.6,22),('AB','validation',1.7,-10),('AA','familiar_test',2.3,15),('AC','transfer_test',1.9,8),('BC','transfer_test',2.2,-15)]
 for typ,split,gap,angle in pairs:
  distance=MODELS[typ[0]]['r']+MODELS[typ[1]]['r']+gap;dx=distance*math.cos(math.radians(angle))/2;dy=distance*math.sin(math.radians(angle))/2
  ts=[dict(type=typ[0],x=round(10-dx,6),y=round(10-dy,6)),dict(type=typ[1],x=round(10+dx,6),y=round(10+dy,6))]
  c=dict(case=f't26_pair_{typ}_{split}',family='pair',split=split,trees=ts,heater_type=typ[0],heater_xy=[ts[0]['x'],ts[0]['y']],strength=1.,duration=20.,gap=gap,bearing=angle)
  rows.append(c)
  rows.append(dict(c,case=c['case'].replace('pair','control'),family='control',trees=ts[1:],matched_pair=c['case']))
 assert all('C' not in [t['type'] for t in c['trees']] for c in rows if c['family']=='pair' and c['split'] in ['train','validation'])
 return rows

def deck(c,ts):
 s=(ROOT/'base-input.fds').read_text()
 for tag in ['HEAD','MESH','TIME','INIT','OBST','VENT','DEVC','SLCF','DUMP','TAIL']:s=re.sub(r'&'+tag+r'\b.*?/','',s,flags=re.S)
 s=s.replace('BNDF_DEFAULT=F','BNDF_DEFAULT=T');s=re.sub(r'MOISTURE_CONTENT\s*=\s*0\.14','MOISTURE_CONTENT = 0.12',s)
 def particle(m):
  b=m[0]
  if "ID='contact ignitor'" in b:return b.replace('AGE=21.',f"AGE={c['duration']+1}.") if isinstance(c['duration'],int) else b.replace('AGE=21.',f"AGE={c['duration']+1}")
  return re.sub(r'QUANTITIES=.*?(?=, STATIC)',"QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR','PARTICLE DIAMETER','INCIDENT HEAT FLUX','PARTICLE CONVECTIVE HEAT FLUX'",b,flags=re.S)
 s=re.sub(r'&PART\b.*?/',particle,s,flags=re.S).replace("T=20., F=1.",f"T={c['duration']}, F=1.").replace("T=20.1, F=0.",f"T={c['duration']+.1}, F=0.")
 a=[f"&HEAD CHID='{c['case']}', TITLE='Frozen particle tree-type transfer pilot' /",'&MESH IJK=40,40,30, XB=0,20,0,20,0,15 /','&TIME T_END=180 /',s,"&MATL ID='generic soil', DENSITY=1500., CONDUCTIVITY=1., SPECIFIC_HEAT=1.2 /","&SURF ID='GROUND', MATL_ID='generic soil', THICKNESS=.5, BACKING='INSULATED' /","&VENT MB='ZMIN', SURF_ID='GROUND' /"]
 for mb in ['XMIN','XMAX','YMIN','YMAX','ZMAX']:a.append(f"&VENT MB='{mb}', SURF_ID='OPEN' /")
 expected=[]
 for i,t in enumerate(c['trees']):
  m=MODELS[t['type']]
  for p in ts[t['type']]['particles']:
   xyz=[p['xyz'][0]+t['x'],p['xyz'][1]+t['y'],p['xyz'][2]];expected.append(dict(instance=i,fuel=p['fuel'],xyz=xyz,weight=p['weight']))
   a.append(f"&INIT PART_ID='{p['fuel']}', XYZ={','.join(f'{v:.8f}' for v in xyz)}, SHAPE='LINE', N_PARTICLES=1, PARTICLE_WEIGHT_FACTOR={p['weight']:.12g} /")
  box=f"{t['x']-m['r']},{t['x']+m['r']},{t['y']-m['r']},{t['y']+m['r']},{m['base']},{m['base']+m['height']}"
  for fuel in CLASSES:
   a.append(f"&DEVC ID='v{i} mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
   a.append(f"&DEVC ID='v{i} fuel {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /")
 for p in ts[c['heater_type']]['heater']:
  xyz=[p['xyz'][0]+c['heater_xy'][0],p['xyz'][1]+c['heater_xy'][1],p['xyz'][2]]
  a.append(f"&INIT PART_ID='contact ignitor', XYZ={','.join(f'{v:.8f}' for v in xyz)}, SHAPE='LINE', N_PARTICLES=1, PARTICLE_WEIGHT_FACTOR={c['strength']} /")
 for q in ['TEMPERATURE','HRRPUV','U-VELOCITY','V-VELOCITY','W-VELOCITY']:a.append(f"&SLCF XB=0,20,0,20,0,15, QUANTITY='{q}', CELL_CENTERED=T /")
 for x in range(20):
  for y in range(20):
   for suffix,q in [('T','WALL TEMPERATURE'),('Q','NET HEAT FLUX')]:a.append(f"&DEVC ID='ground_{x}_{y}_{suffix}', XYZ={x+.5},{y+.5},0, IOR=3, QUANTITY='{q}' /")
 a.extend(['&DUMP DT_DEVC=1., DT_HRR=1., DT_BNDF=2., DT_SLCF=2., DT_PART=2., DT_RESTART=30., SMOKE3D=F /','&TAIL /'])
 return '\n'.join(a)+'\n',expected

def main():
 assert not (ROOT/'budget.json').exists(),'Cannot regenerate reserved inputs'
 ts=templates();dump(ROOT/'data/tree-templates.json',ts);rows=manifest()
 for c in rows:
  s,expected=deck(c,ts);(ROOT/'decks'/f"{c['case']}.fds").write_text(s)
  c.update(deck_sha256=sha(s.encode()),horizon_s=180,variant='passive',profile=False,solve_limit_s=1500,dx=.5)
 freeze=dict(template_sha256=sha((ROOT/'data/tree-templates.json').read_bytes()),templates={k:sha(json.dumps(v,sort_keys=True).encode()) for k,v in ts.items()},cases={c['case']:c['deck_sha256'] for c in rows},rule='Translate only. Never resample, rotate, change weights, or regenerate after reservation; source strength is predeclared heater weight only.')
 dump(ROOT/'cases.json',rows);dump(ROOT/'results/input-freeze.json',freeze)
 print('Prepared',len(rows),'cases; no simulation submitted')
if __name__=='__main__':main()
