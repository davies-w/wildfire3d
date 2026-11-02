"""Prepare the authorized factorial design; no cloud submission or FDS execution."""
from pathlib import Path
import gzip,json,math,hashlib
import numpy as np
R=Path(__file__).resolve().parent;D=R/'data';D.mkdir(exist_ok=True)
src=json.loads((R.parent/'47_tree_archetypes/data/geometry.json').read_text())
angles=list(range(0,360,45));species={1:src['trees'][0],3:src['trees'][2]};geometries=[]
def crown_boundary(g,z,angle):
 # Support point of the union's horizontal section in the requested compass direction.
 n=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))]);pts=[]
 for x,y,b,h,r in g['cones']:
  if b<=z<=h:pts.append(np.array([x,y])+r*(h-z)/(h-b)*n)
 for x,y,cz,rx,ry,rz in g['ellipsoids']:
  q=1-((z-cz)/rz)**2
  if q>0:
   aa,bb=rx*math.sqrt(q),ry*math.sqrt(q);v=np.array([aa*aa*n[0],bb*bb*n[1]])/math.sqrt((aa*n[0])**2+(bb*n[1])**2);pts.append(np.array([x,y])+v)
 assert pts,'Requested crown slice contains no foliage'
 p=max(pts,key=lambda p:float(p@n));return [float(p[0]),float(p[1]),float(z)]
for typ,t in species.items():
 nominal_h=20 if typ==1 else 24;base=6 if typ==1 else 12;nominal_r=3.5 if typ==1 else 5.5
 for dr in range(-2,3):
  for dh in range(-2,3):
   h=nominal_h+dh;r=nominal_r+dr;xy=r/nominal_r;zz=(h-base)/(nominal_h-base)
   g=dict(id=f't{typ}_r{r:g}_h{h:g}',type_id=typ,name=t['name'],total_height_m=h,crown_base_m=base,crown_radius_m=r,radius_definition='half of total x crown width; uniform x/y scaling of entire crown arrangement',cones=[],ellipsoids=[])
   for x,y,b,top,rad in t['cones']:g['cones'].append([x*xy,y*xy,base+(b-base)*zz,base+(top-base)*zz,rad*xy])
   for x,y,z,rx,ry,rz in t['ellipsoids']:g['ellipsoids'].append([x*xy,y*xy,base+(z-base)*zz,rx*xy,ry*xy,rz*zz])
   # Stems retained as geometry; combustion/bark properties are not invented.
   g['stems']=[]
   for start,end,rad in t['stems']:
    def transform(p):return [p[0]*xy,p[1]*xy,p[2] if p[2]<=base else base+(p[2]-base)*zz]
    g['stems'].append([transform(start),transform(end),rad])
   g['ignitions']=[]
   for mode,levels in [('base',[.25,.75,1.25]),('crown',[.1,.5,.9])]:
    for lev in levels:
     z=lev if mode=='base' else base+lev*(h-base)
     for angle in angles:
      if mode=='base':
       a,b,rad=g['stems'][0];f=(z-a[2])/(b[2]-a[2]);cx=a[0]+f*(b[0]-a[0]);cy=a[1]+f*(b[1]-a[1]);point=[cx+rad*math.cos(math.radians(angle)),cy+rad*math.sin(math.radians(angle)),z]
      else:point=crown_boundary(g,z,angle)
      g['ignitions'].append(dict(mode=mode,level=lev,compass_deg=angle,contact_xyz_m=point))
   assert len(g['ignitions'])==48;geometries.append(g)
count=0;rows=[];rng=np.random.default_rng(4803516)
for gi,g in enumerate(geometries):
 # Twenty unique locations from each family. Across both families each angle occurs five times.
 omit_base=set(rng.choice(8,4,replace=False).tolist())
 for mode in range(2):
  omitted=sorted(omit_base if mode==0 else set(range(8))-omit_base)
  levels=rng.permutation([0,1,2,(gi+mode)%3]);drop={(int(lev),ang) for lev,ang in zip(levels,omitted)}
  locations=[mode*24+lev*8+ang for lev in range(3) for ang in range(8) if (lev,ang) not in drop]
  rng.shuffle(locations)
  winds=rng.permutation(np.tile([1,2,3,4,5],4))
  moistures=rng.permutation(np.tile([.06,.12,.18,.24,.30],4))
  loadings=rng.permutation(np.array([.7,1.,1.3])[(np.arange(20)+gi+mode)%3])
  for ii,wind,moisture,loading in zip(locations,winds,moistures,loadings):
   rows.append(dict(case=f'tree48_{count:06d}',geometry_id=g['id'],type_id=g['type_id'],ignition_index=int(ii),wind_m_s=int(wind),moisture_fraction=float(moisture),loading_multiplier=float(loading),seed=4800000+count));count+=1
assert count==2000 and len(geometries)==50
for g in geometries:
 r=[v for v in rows if v['geometry_id']==g['id']];assert len(r)==40
 assert len({v['ignition_index'] for v in r})==40
 for mode in range(2):
  m=[v for v in r if v['ignition_index']//24==mode];assert len(m)==20
  for w in range(1,6):assert sum(v['wind_m_s']==w for v in m)==4
  for level in range(3):assert 6<=sum((v['ignition_index']%24)//8==level for v in m)<=7
 for angle in range(8):assert sum(v['ignition_index']%8==angle for v in r)==5
with (D/'cases.jsonl.gz').open('wb') as raw:
 with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as f:
  for row in rows:f.write((json.dumps(row,separators=(',',':'))+'\n').encode())
(D/'geometries.json').write_text(json.dumps(geometries,indent=2)+'\n')
external=['tree_height_m','crown_radius_m','crown_base_m','loading_multiplier','wind_x_m_s','initial_water_kg','initial_unreacted_fuel_kg','ignition_x_m','ignition_y_m','ignition_z_m','ignition_is_crown','ignition_on_fraction','dt_s']+[f'type_{i}' for i in range(1,6)]
summary=dict(status='DESIGN ONLY: no executable FDS decks, reservations or submission',examples=count,geometries=50,examples_per_type=1000,sampling_seed=4803516,sampling="Balanced random design:40 per geometry,20 per ignition family; not full factorial",examples_per_geometry=40,type_ids={'1':'Ponderosa pine','2':'Coast live oak','3':'Blue gum eucalyptus','4':'Italian cypress','5':'Manzanita'},sampled_types=[1,3],ignition_patches_per_example=1,ignition_families_mutually_exclusive=True,angles_deg=angles,base_heights_m=[.25,.75,1.25],crown_height_fractions=[.1,.5,.9],wind_m_s=[1,2,3,4,5],moisture=[.06,.12,.18,.24,.30],loading=[.7,1,1.3],horizon_s=180,nominal_saved_interval_s=2,model=dict(history_steps=8,state_values=10,feedback='all ten predictions',external_names=external,type_encoding='five one-hot features, not ordinal scalar; unseen types untrained',curriculum_steps=[1,8,16,32,64,90],curriculum_start_epochs=[1,21,41,61,110,130],min_epochs=160,max_epochs=400,patience=30),draft_domain_m=[48,32,40],draft_cell_size_m=.5,draft_cells=491520,old_cells=49152,domain_validation_required=True,open_physics=['Executable source patch size/power and contact-overlap audit','Base ignition uses imposed20-second heating as approved, with no grass fuel model','Stem/bark fuel representation must be specified','Crown fuel masses/particle density and union-overlap validation','Larger-domain and mesh sensitivity; 180 s duration sufficiency','Cone extraction scales and search range must be extended for taller trees'],split='Not assigned: group replicas and reserve geometry/environment combinations before simulations or tuning',manifest_sha256=hashlib.sha256((D/'cases.jsonl.gz').read_bytes()).hexdigest())
(D/'design.json').write_text(json.dumps(summary,indent=2)+'\n');print(count,'cases; 50 geometries; mutually exclusive base/crown ignition')
