"""Offline campaign decks for1978 new cases. Never runs FDS."""
from pathlib import Path
import gzip,json,math,re,hashlib
import numpy as np
R=Path(__file__).resolve().parent;D=R/'data/decks';D.mkdir(parents=True,exist_ok=True);(D/'decks').mkdir(exist_ok=True)
G={g['id']:g for g in json.loads((R/'data/geometries.json').read_text())};rows=[json.loads(s) for s in gzip.open(R/'data/cases.jsonl.gz','rt')]
CLASSES=[('foliage',3940.,.05,1.683),('small roundwood',2667.,.1,.289),('medium roundwood',888.,.1,.263),('large roundwood',500.,.1,.394)]
base=(R.parent/'36_tree_density/base-input.fds').read_text();blocks=re.findall(r'&\w+\b.*?/',base,re.S);allowed=[]
for b in blocks:
 tag=re.match(r'&(\w+)',b)[1]
 if tag in ['REAC','SPEC'] or (tag=='MATL' and any(f"'{n}'" in b for n in ['GENERIC VEGETATION','CHAR','ASH'])) or (tag=='RAMP' and "'c_v'" in b):allowed.append(b)
 if tag in ['SURF','PART'] and any(re.search(r"ID\s*=\s*'"+re.escape(n)+"'",b) for n,_,_,_ in CLASSES):allowed.append(b)
 if tag in ['SURF','PART','RAMP'] and any(re.search(r"ID\s*=\s*'"+n+"'",b) for n in ['contact burner','contact ignitor','contact']):allowed.append(b)
material='\n'.join(allowed);assert material.count('MOISTURE_CONTENT')==4
assert not (R/'private/submission-intent.json').exists()
chosen=[dict(c,variant='baseline') for c in rows if c['reuse'] is None]
assert len(chosen)==1978

def inside(g,p):
 mask=np.zeros(len(p),bool)
 for x,y,b,h,r in g['cones']:
  z=p[:,2];mask|=(z>=b)&(z<=h)&((p[:,0]-x)**2+(p[:,1]-y)**2<=(r*(h-z)/(h-b))**2)
 for x,y,z,rx,ry,rz in g['ellipsoids']:mask|=(((p-np.array([x,y,z]))/np.array([rx,ry,rz]))**2).sum(axis=1)<=1
 return mask

def crown_samples(g):
 boxes=[]
 for x,y,b,h,r in g['cones']:boxes.append([x-r,x+r,y-r,y+r,b,h])
 for x,y,z,rx,ry,rz in g['ellipsoids']:boxes.append([x-rx,x+rx,y-ry,y+ry,z-rz,z+rz])
 b=np.array(boxes);lo=np.floor(b[:,[0,2,4]].min(axis=0)*2)/2;hi=np.ceil(b[:,[1,3,5]].max(axis=0)*2)/2
 centers=np.array(np.meshgrid(*[np.arange(l,h,.5)+.25 for l,h in zip(lo,hi)],indexing='ij')).reshape(3,-1).T
 offsets=np.array(np.meshgrid(*[np.array([-.1875,-.0625,.0625,.1875])]*3,indexing='ij')).reshape(3,-1).T
 points=[];vol=[]
 for start in range(0,len(centers),1000):
  cs=centers[start:start+1000];ps=cs[:,None,:]+offsets;ok=inside(g,ps.reshape(-1,3)).reshape(len(cs),64);good=ok.any(axis=1)
  # One representative inside the actual union;64subcells give fractional boundary volume.
  for c,pp,m in zip(cs[good],ps[good],ok[good]):points.append(pp[np.flatnonzero(m)[np.argmin(np.linalg.norm(pp[m]-c,axis=1))]]);vol.append(float(m.mean()*.125))
 return np.array(points),np.array(vol)
cache={};audits=[];outcases=[]
for j,v in enumerate(chosen):
 import shutil
 assert shutil.disk_usage(R).free>4*1024**3,'Insufficient free disk for remaining decks'
 if j%50==0:print('Preparing',j,'of',len(chosen),flush=True)
 g=G[v['geometry_id']];ig=g['ignitions'][v['ignition_index']];name=v['case']+'_'+v['variant'];dx=v['dx'];dom=v['domain'];origin=np.array([dom[0]/2,dom[1]/2,0]);contact=np.array(ig['contact_xyz_m']);angle=math.radians(ig['compass_deg']);normal=np.array([math.cos(angle),math.sin(angle),0]);tangent=np.array([-normal[1],normal[0],0])
 if g['id'] not in cache:cache[g['id']]=crown_samples(g)
 points,vol=cache[g['id']];points=points.copy();anchor_shift=None
 if ig['mode']=='crown':
  # Move one cell representative just inside foliage at the igniter; no mass is added.
  anchor=contact-.02*normal;assert inside(g,anchor[None])[0]
  near=int(np.argmin(np.linalg.norm(points-anchor,axis=1)));anchor_shift=float(np.linalg.norm(points[near]-anchor));assert anchor_shift<.75;points[near]=anchor
 assert inside(g,points).all();assert np.all(vol>0)
 s=[f"&HEAD CHID='{name}', TITLE='Single species-inspired geometry, generic vegetation and wood' /",f"&MESH IJK={','.join(str(round(a/dx)) for a in dom)}, XB=0,{dom[0]},0,{dom[1]},0,{dom[2]} /",'&TIME T_END=180 /',f"&MISC RND_SEED={v['seed']}, BNDF_DEFAULT=T /",f"&WIND SPEED={v['wind_m_s']}, DIRECTION=270. /",re.sub(r'MOISTURE_CONTENT\s*=\s*[\d.]+',f"MOISTURE_CONTENT={v['moisture_fraction']}",material)]
 # Emit static weighted particle elements, not voxel-sized solid crown blocks.
 # Only replace the four vegetation PART blocks, retaining the igniter's distinct output list.
 for n,_,_,_ in CLASSES:
  s[-1]=re.sub(r"(&PART ID='"+n+r"'.*?QUANTITIES=).*?(, STATIC)",r"\1'PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR','PARTICLE DIAMETER','INCIDENT HEAT FLUX','PARTICLE CONVECTIVE HEAT FLUX'\2",s[-1],flags=re.S)
 expected={}
 for n,sigma,L,density in CLASSES:
  mass=500*math.pi*(2/sigma)**2*L;weights=vol*density*v['loading_multiplier']/mass;expected[n]=float((vol*density*v['loading_multiplier']).sum())
  for p,w in zip(points+origin,weights):s.append(f"&INIT PART_ID='{n}', XYZ={','.join(f'{x:.8f}' for x in p)}, SHAPE='LINE', N_PARTICLES=1, PARTICLE_WEIGHT_FACTOR={w:.12g} /")
 # Explicit main stems use cylindrical thermal elements along their drawn axes.
 stem_xyz=[];stem_mass=0
 for bi,(a,b,rad) in enumerate(g['stems']):
  a,b=np.array(a),np.array(b);length=float(np.linalg.norm(b-a));nseg=math.ceil(length/.25);L=length/nseg;sid=f'wood stem {bi}'
  s.append(f"&SURF ID='{sid}', MATL_ID='GENERIC VEGETATION', MOISTURE_CONTENT={v['moisture_fraction']}, SURFACE_VOLUME_RATIO={2/rad:.12g}, LENGTH={L:.12g}, GEOMETRY='CYLINDRICAL' /")
  s.append(f"&PART ID='{sid}', SURF_ID='{sid}', DRAG_COEFFICIENT=2.8, STATIC=T, SAMPLING_FACTOR=1, QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR','PARTICLE DIAMETER','INCIDENT HEAT FLUX','PARTICLE CONVECTIVE HEAT FLUX' /")
  for k in range(nseg):
   p=a+(b-a)*(k+.5)/nseg;stem_xyz.append(p);s.append(f"&INIT PART_ID='{sid}', XYZ={','.join(f'{x:.8f}' for x in p+origin)}, SHAPE='LINE', N_PARTICLES=1, PARTICLE_WEIGHT_FACTOR=1. /")
  expected[sid]=500*math.pi*rad**2*length;stem_mass+=expected[sid]
 # Constant0.4x0.4m tangent-plane patch: same1600particles and individual source recipe as prior run.
 patch=np.array([contact+.02*normal+tangent*u+np.array([0,0,w]) for u in np.linspace(-.195,.195,40) for w in np.linspace(-.195,.195,40)])
 assert patch[:,2].min()>0
 for p in patch+origin:s.append(f"&INIT PART_ID='contact ignitor', XYZ={','.join(f'{x:.8f}' for x in p)}, SHAPE='LINE', N_PARTICLES=1, PARTICLE_WEIGHT_FACTOR=1. /")
 allpoints=np.vstack([points,np.array(stem_xyz),patch])+origin;assert (allpoints>0).all() and (allpoints<np.array(dom)).all()
 s+= ["&MATL ID='generic soil', DENSITY=1500., CONDUCTIVITY=1., SPECIFIC_HEAT=1.2 /","&SURF ID='GROUND', MATL_ID='generic soil', THICKNESS=.5, BACKING='INSULATED' /","&VENT MB='ZMIN', SURF_ID='GROUND' /"]
 for face in ['XMIN','XMAX','YMIN','YMAX','ZMAX']:s.append(f"&VENT MB='{face}', SURF_ID='OPEN' /")
 xb=f'0,{dom[0]},0,{dom[1]},0,{dom[2]}'
 for n in expected:
  s.extend([f"&DEVC ID='{n} mass', QUANTITY='MPUV', PART_ID='{n}', XB={xb}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /",f"&DEVC ID='{n} vapor', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{n}', SURF_ID='{n}', XB={xb}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /"])
 s.extend([f"&SLCF XB={xb}, QUANTITY='TEMPERATURE', CELL_CENTERED=T /",f"&SLCF PBY={origin[1]}, QUANTITY='HRRPUV', CELL_CENTERED=T /","&DUMP DT_DEVC=1., DT_HRR=1., DT_PART=2., DT_SLCF=2., DT_SL3D=36., DT_RESTART=30., SMOKE3D=F /",'&TAIL /'])
 deck='\n'.join(s)+'\n';path=D/'decks'/f'{name}.fds';path.write_text(deck)
 assert deck.count("PART_ID='contact ignitor', XYZ=")==1600
 assert deck.count('&MESH ')==1 and deck.count('&TIME ')==1 and '&OBST ' not in deck
 nearest=float(np.linalg.norm(points-contact,axis=1).min()) if ig['mode']=='crown' else float(np.min(np.maximum(0,np.linalg.norm(np.array(stem_xyz)-contact,axis=1)-g['stems'][0][2])))
 assert nearest<.15
 audit=dict(case=name,geometry_id=g['id'],mode=ig['mode'],contact_xyz_local_m=contact.tolist(),origin_m=origin.tolist(),crown_union_volume_m3=float(vol.sum()),crown_elements_per_class=len(points),stem_elements=len(stem_xyz),expected_dry_mass_kg=expected,expected_wet_mass_kg={k:m*(1+v['moisture_fraction']) for k,m in expected.items()},crown_anchor_shift_m=anchor_shift,contact_distance_m=nearest,cells=int(np.prod(np.array(dom)/dx)),deck_sha256=hashlib.sha256(deck.encode()).hexdigest(),passed=True)
 audits.append(audit);outcases.append(dict(v,pilot_case=name,deck_sha256=audit['deck_sha256'],ignition=ig,expected_wet_mass_kg=audit['expected_wet_mass_kg']))
(D/'cases.json').write_text(json.dumps(outcases,indent=2)+'\n');(D/'validation.json').write_text(json.dumps(dict(passed=True,scope='Offline geometry, mass accounting and input structure only; actual FDS parse/mass/restart checks pending in cloud',cases=audits),indent=2)+'\n')
print('Prepared',len(outcases),'pilot decks; all offline checks pass; no solver executed')
