"""Extract requested and mesh-snapped obstruction bounds from saved SMV metadata."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cases={}
for case,spacing in [('hot_a',.5),('hot_coarse',1.)]:
 lines=(ROOT/'data/cloud'/case/(case+'.smv')).read_text().splitlines()
 start=lines.index('OBST');n=int(lines[start+1]);requested=lines[start+2:start+2+n];indices=lines[start+2+n:start+2+2*n]
 cases[case]=[{'obstacle':i+1,'requested_bounds_m':list(map(float,a.split()[:6])),'snapped_bounds_m':[int(v)*spacing for v in b.split()[:6]]} for i,(a,b) in enumerate(zip(requested,indices))]
changes=[]
for a,b in zip(cases['hot_a'],cases['hot_coarse']):
 if a['snapped_bounds_m']!=b['snapped_bounds_m']:changes.append({'obstacle':a['obstacle'],'baseline_bounds_m':a['snapped_bounds_m'],'coarse_bounds_m':b['snapped_bounds_m']})
result={'assumption':'These two saved single meshes are uniform, origin zero, and spacings 0.5 and 1 m respectively. SMV obstruction integer indices map to physical grid coordinates. Zero thickness does not imply an obstruction was removed.','cases':cases,'changed_obstructions':changes}
(ROOT/'results/geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(changes,indent=2))
