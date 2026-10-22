"""Freeze geometry-only composition targets before fitting; never reads FDS outcomes."""
import hashlib,json
from shapely.geometry import shape,mapping
from shapely.affinity import translate
from scene import ROOT
out=ROOT/'component-heldout-geometry.json'
assert not out.exists(),'Never overwrite frozen geometry'
rows=[]
for name,gap,height,wind,moisture in [('santa_rosa_east_03',1,5,270,.14),('glen_ellen_06',4,6,225,.20)]:
 p=ROOT.parent/'14_ignition_surrogate/data/scenes'/name/'scene.json';d=json.loads(p.read_text());poly=shape(d['main_structure']['footprint']);poly=translate(poly,xoff=24-poly.centroid.x,yoff=24-poly.centroid.y);west=poly.bounds[0];x=west-2-gap
 crowns=[dict(id='v0',x=x-5,y=24,base=3,height=7,radius=2,initialized=True),dict(id='v1',x=x,y=19,base=3,height=7,radius=2,initialized=False),dict(id='v2',x=x-.5,y=29,base=5,height=11,radius=3,initialized=False)]
 assert min(c['x']-c['radius'] for c in crowns)>0
 rows.append(dict(case='c21_'+name,source_scene_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),footprint_local=mapping(poly),building_height_m=height,canopies=crowns,domain_m=[0,48,0,48,0,24],dx_m=.5,horizon_s=90,wind_speed_m_s=3,wind_direction_deg=wind,moisture=moisture,seed=4321,scope='Actual recorded Sonoma building footprint translated to domain centre; assigned flat height and three synthetic canopy patches. Canopy positions are deliberately assigned, not measured from this property. Generic wood building/vegetation, no interiors/trunks/groundcover/embers.'))
record=dict(status='geometry_frozen_no_simulation',scenes=rows,rule='Train only on small configurations. Freeze model/additive baseline and full autonomous predictions with hashes before submitting or reading any test FDS outputs. No test-driven geometry changes.',limitations='Only2 scenes,90s. Full footprint extrusions introduce roofs/opposite walls absent or underrepresented in current local training; quantify coverage before deployment. This is a fixed-resolution composition challenge, not real-property risk validation.')
text=json.dumps(record,indent=2);out.write_text(text);(ROOT/'results/component-heldout-geometry-sha256.json').write_text(json.dumps(dict(sha256=hashlib.sha256(text.encode()).hexdigest(),file=out.name),indent=2));print('Frozen two geometry-only test scenes')
