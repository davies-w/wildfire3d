"""Check physical splits across BOTH reused and new data, not just case identifiers."""
from pathlib import Path
import json
R=Path(__file__).parent
rows=json.loads((R/'development.json').read_text())+json.loads((R/'fresh-tests.json').read_text())
def physical(c):
 return tuple(round(float(v),8) for v in [c.get('crown_height_m',8),c['moisture'],c.get('loading_multiplier',1),c['wind_speed'],c['angle_deg']])
groups={}
for c in rows:groups.setdefault(physical(c),[]).append(c)
assert all(len({c['split'] for c in group})==1 for group in groups.values())
assert len(groups)==480
counts={split:sum(group[0]['split']==split for group in groups.values()) for split in ['train','validation','test']}
assert counts==dict(train=400,validation=40,test=40)
result=dict(passed=True,unique_physical_configurations=480,trajectories=len(rows),unique_by_split=counts,cross_split_overlap=0,reused_rows=sum(not c['new_geometry'] for c in rows),matching_dimensions=['crown height','moisture dry basis','loading multiplier','wind speed','ignition angle'],legacy_defaults='Original s27 cone height8m/loading1; same frozen generic material/geometry family')
(R/'results/full-split-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
