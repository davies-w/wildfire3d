"""Verify oak wall clearances against corresponding compact pine/eucalyptus variants."""
from pathlib import Path
import json,math
R=Path(__file__).resolve().parent
new=json.loads((R/'data/geometries.json').read_text());old=json.loads((R.parent/'48_two_tree_design/data/geometries.json').read_text())
def bounds(g):
 b=[[x-r,x+r,y-r,y+r] for x,y,z,h,r in g['cones']]+[[x-rx,x+rx,y-ry,y+ry] for x,y,z,rx,ry,rz in g['ellipsoids']]
 return [min(v[i] for v in b) if i%2==0 else max(v[i] for v in b) for i in range(4)]
def margins(g,xy):
 b=bounds(g);return [xy[0]/2+b[0],xy[0]/2-b[1],xy[1]/2+b[2],xy[1]/2-b[3]]
rows=[]
for g in new:
 dr=g['crown_radius_m']-6;dh=g['total_height_m']-10;m=margins(g,[29,20]);refs=[]
 for typ,h,r in [(1,20,3.5),(3,24,5.5)]:
  q=next(x for x in old if x['type_id']==typ and x['crown_radius_m']==r+dr and x['total_height_m']==h+dh);v=margins(q,[24,16]);assert all(a+1e-9>=b for a,b in zip(m,v));refs.append(dict(geometry_id=q['id'],wall_clearance_m=v))
 rows.append(dict(geometry_id=g['id'],oak_wall_clearance_m=m,references=refs))
assert len(rows)==25
(R/'data/clearance.json').write_text(json.dumps(dict(passed=True,wall_order=['xmin','xmax','ymin','ymax'],oak_xy_m=[29,20],reference_xy_m=[24,16],cases=rows,scope='Geometric per-wall clearance only, not numerical boundary validation'),indent=2)+'\n')
print('All25 oak variants match or exceed both reference clearances')
