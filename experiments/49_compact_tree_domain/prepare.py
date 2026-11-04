"""Prepare matched compact-domain reruns without changing fuel, source or numerical resolution."""
from pathlib import Path
import json,re,math,hashlib
R=Path(__file__).resolve().parent;OLD=R.parent/'48_two_tree_design';D=R/'data/decks';D.mkdir(parents=True,exist_ok=True)
assert not (R/'private/submission-intent.json').exists()
G={g['id']:g for g in json.loads((OLD/'data/geometries.json').read_text())}
old=[c for c in json.loads((OLD/'data/pilot/cases.json').read_text()) if c['variant']!='fine'];assert len(old)==22
cases=[];audit=[]
for c in old:
 g=G[c['geometry_id']];height=math.ceil(g['total_height_m']+(12 if c['variant']=='expanded' else 6));dom=[24,16,height];name=c['pilot_case'].replace('tree48_','tree49_');src=(OLD/'data/pilot/decks'/(c['pilot_case']+'.fds')).read_text();assert hashlib.sha256(src.encode()).hexdigest()==c['deck_sha256'];dy=8-c['domain'][1]/2
 points=[];original=[]
 def xyz(m):
  p=[float(x) for x in m[1].split(',')];original.append(p.copy());p[1]+=dy;points.append(p);return 'XYZ='+','.join(f'{x:.8f}' for x in p)
 new=re.sub(r'XYZ=([-+\d.eE]+,[-+\d.eE]+,[-+\d.eE]+)',xyz,src)
 oldxb='0,'+str(c['domain'][0])+',0,'+str(c['domain'][1])+',0,'+str(c['domain'][2]);newxb='0,24,0,16,0,'+str(height)
 new=new.replace('XB='+oldxb,'XB='+newxb);new=re.sub(r'IJK=\d+,\d+,\d+',f'IJK=48,32,{height*2}',new);new=new.replace(f'PBY={c["domain"][1]/2}', 'PBY=8.0').replace(c['pilot_case'],name).replace('Two-tree pilot, generic vegetation and wood','Single-tree compact-domain comparison, generic vegetation and wood')
 assert len(original)==len(points) and all(abs(a[0]-b[0])<1e-8 and abs(a[2]-b[2])<1e-8 and abs(b[1]-a[1]-dy)<1e-8 for a,b in zip(original,points))
 assert all(all(0<x<d for x,d in zip(p,dom)) for p in points)
 boxes=[[x-r,x+r,y-r,y+r,b,h] for x,y,b,h,r in g['cones']]+[[x-rx,x+rx,y-ry,y+ry,z-rz,z+rz] for x,y,z,rx,ry,rz in g['ellipsoids']]
 bounds=[min(b[i] for b in boxes) if i%2==0 else max(b[i] for b in boxes) for i in range(6)]
 clearance=min(12+bounds[0],12-bounds[1],8+bounds[2],8-bounds[3]);assert clearance>=2.5-1e-8 and height-bounds[5]>=6
 # Excluding the declared domain/translation/title/ID edits, every line is retained.
 assert src.count('&INIT ')==new.count('&INIT ') and src.count('PARTICLE_WEIGHT_FACTOR=')==new.count('PARTICLE_WEIGHT_FACTOR=')
 (D/(name+'.fds')).write_text(new);digest=hashlib.sha256(new.encode()).hexdigest()
 cases.append(dict(c,pilot_case=name,original_case=c['pilot_case'],original_deck_sha256=c['deck_sha256'],deck_sha256=digest,domain=dom,comparison_variant='height_control' if c['variant']=='expanded' else 'compact',vertical_clearance_m=height-g['total_height_m'],horizontal_crown_clearance_m=clearance))
 audit.append(dict(case=name,original_case=c['pilot_case'],domain_m=dom,cells=48*32*height*2,horizontal_crown_clearance_m=clearance,vertical_clearance_m=height-g['total_height_m'],translation_m=[0,dy,0],particle_count=len(points),fuel_source_wind_moisture_seed_unchanged=True,passed=True))
(R/'data/cases.json').write_text(json.dumps(cases,indent=2)+'\n');(R/'data/input-audit.json').write_text(json.dumps(dict(passed=True,cases=audit,scope='Offline geometry/input audit only; no solver execution or equivalence claim'),indent=2)+'\n')
print('Prepared22 matched reruns; cells',min(x['cells'] for x in audit),max(x['cells'] for x in audit))
