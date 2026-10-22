"""Geometry-only Stage C decks. Never solves or reads test outputs."""
import hashlib,json,re
from shapely.geometry import shape,Point
from scene import ROOT,CLASSES

def prepare():
 source=ROOT/'component-heldout-geometry.json';frozen=json.loads(source.read_text());expected=json.loads((ROOT/'results/component-heldout-geometry-sha256.json').read_text())['sha256'];assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
 records=[]
 for c in frozen['scenes']:
  name=c['case'];s=(ROOT/'decks/b21_single_1.fds').read_text();s=re.sub(r"CHID='[^']+'",f"CHID='{name}'",s,count=1);s=re.sub(r'&MESH\b.*?/', '&MESH IJK=96,96,48, XB=0,48,0,48,0,24 /',s,flags=re.S);s=re.sub(r'&WIND\b.*?/',f"&WIND SPEED={c['wind_speed_m_s']}, DIRECTION={c['wind_direction_deg']} /",s,flags=re.S);s=re.sub(r'MOISTURE_CONTENT\s*=\s*[0-9.]+',f"MOISTURE_CONTENT = {c['moisture']}",s)
  s=re.sub(r'&(?:OBST|INIT|DEVC)\b.*?/','',s,flags=re.S)
  poly=shape(c['footprint_local']);cells={(i,j) for i in range(96) for j in range(96) if poly.covers(Point((i+.5)*.5,(j+.5)*.5))};h=c['building_height_m'];extra=[];patches=[];boxes=[]
  for j in range(96):
   xs=sorted(i for i,jj in cells if jj==j)
   while xs:
    start=end=xs.pop(0)
    while xs and xs[0]==end+1:end=xs.pop(0)
    box=[start*.5,(end+1)*.5,j*.5,(j+1)*.5,0,h];boxes.append(box);extra.append(f"&OBST XB={','.join(map(str,box))}, SURF_ID='HOUSE', BNDF_OBST=T /")
  def probe(x,y,z,normal,ior,area):
   stem=f'q{len(patches)}';patches.append(dict(id=stem,xyz=[x,y,z],normal=normal,area=area))
   for suffix,q in [('temp','WALL TEMPERATURE'),('rad_in','INCIDENT HEAT FLUX'),('conv','CONVECTIVE HEAT FLUX'),('burn','BURNING RATE')]:extra.append(f"&DEVC ID='{stem}_{suffix}', XYZ={x},{y},{z}, IOR={ior}, QUANTITY='{q}' /")
  for i,j in sorted(cells):
   # Roof quadrature represents four .5m cells where possible; sparse samples
   # cannot replace the whole-structure maximum and raw boundary ignition check.
   if i%2==0 and j%2==0:probe((i+.5)*.5,(j+.5)*.5,h,[0,0,1],3,1.)
   for di,dj,normal,ior in [(-1,0,[-1,0,0],-1),(1,0,[1,0,0],1),(0,-1,[0,-1,0],-2),(0,1,[0,1,0],2)]:
    if (i+di,j+dj) not in cells:
     for z in [.5+k for k in range(int(h))]:probe((i+.5+di*.5)*.5,(j+.5+dj*.5)*.5,z,normal,ior,.5)
  for n in c['canopies']:
   x,y,z,r,ch=[n[k] for k in ['x','y','base','radius','height']];box=f'{x-r},{x+r},{y-r},{y+r},{z},{z+ch}'
   for fuel,density in CLASSES:
    extra.append(f"&INIT PART_ID='{fuel}', XYZ={x},{y},{z}, RADIUS={r}, HEIGHT={ch}, SHAPE='CONE', N_PARTICLES_PER_CELL=1, DRY=T, MASS_PER_VOLUME={density} /")
    extra.append(f"&DEVC ID='{n['id']} mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
    extra.append(f"&DEVC ID='{n['id']} fuel {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /")
   if n['initialized']:extra.append(f"&INIT PART_ID='contact ignitor', XYZ={x},{y},{z+.1}, RADIUS={r*.75}, SHAPE='RING', N_PARTICLES=1600 /")
  for stem,q in [('house_max','WALL TEMPERATURE'),('house_burn_max','BURNING RATE')]:extra.append(f"&DEVC ID='{stem}', QUANTITY='{q}', SURF_ID='HOUSE', XB=0,48,0,48,0,24, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /")
  s=s.replace('&TAIL /','\n'.join(extra)+'\n&TAIL /');p=ROOT/'decks'/f'{name}.fds'
  if p.exists():assert p.read_text()==s,'Do not overwrite changed test deck'
  else:p.write_text(s)
  records.append(dict(c,split='test',deck_sha256=hashlib.sha256(s.encode()).hexdigest(),building_boxes=boxes,extra_surface_patches=patches,voxel_footprint_area_m2=len(cells)*.25,recorded_footprint_area_m2=poly.area,measurement_note='Sparse1m vertical wall samples and approximately1m roof samples; global surface maximum and full raw boundary fields retain any-part ignition criterion. Staircase0.5m voxel footprint, solid extrusion without interior. Roof patch weights approximate edge coverage.'))
 (ROOT/'component-test-inputs.json').write_text(json.dumps(dict(status='prepared_no_solve',frozen_geometry_sha256=expected,cases=records),indent=2));print([(c['case'],len(c['extra_surface_patches'])) for c in records])
if __name__=='__main__':prepare()
