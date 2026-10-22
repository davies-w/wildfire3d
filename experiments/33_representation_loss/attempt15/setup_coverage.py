"""Fixed strength-stratified TRAIN subset; no validation target selection."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;S=R.parent.parent/'32_tree_expansion'
cs=json.loads((S/'development.json').read_text());metrics=json.loads((R.parent/'attempt14/results/coverage-summary.json').read_text())['configuration_metrics']
mm={x['configuration']:x['metrics']['truth_mean_HRR_kW'] for x in metrics if x['arm']=='expand360' and x['stage']=='final' and x['cohort']=='all_train360' and x['window']=='post_source'}
rng=np.random.default_rng(3315);names=[]
for lo,hi in [(0,1),(1,10),(10,100),(100,float('inf'))]:
 pool=sorted(n for n,v in mm.items() if lo<=v<hi);names+=list(rng.choice(pool,12,replace=False))
train=[c for c in cs if c['split']=='train' and c['new_geometry'] and c['replica']==0 and c['configuration'] in names];val=[c for c in cs if c['split']=='validation' and c['new_geometry']];chosen=train+val
assert len(train)==48 and len(val)==40
(R/'cases.json').write_text(json.dumps(chosen,indent=2));case_names={c['case'] for c in chosen};groups=json.loads((S/'groups.json').read_text());(R/'groups.json').write_text(json.dumps([g for g in groups if case_names.intersection(g['cases'])],indent=2));z=np.load(S/'data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{n:z[n] for n in case_names})
(R/'coverage-plan.json').write_text(json.dumps(dict(train_configurations=sorted(names),validation_configurations=sorted({c['configuration'] for c in val}),animation_cases=['x32_360_s0','x32_368_s0','x32_376_s0','x32_384_s0'],scope='48 strength-stratified training configurations,12 each truth-HRR band <1/1-10/10-100/>=100kW;32 existing development validation configs40trajectories. Same4000updates/schedule/initial14expanded model and optimizer; physical_low control versus added absolute total-HRR error/(truth+10kW) weights.02/.1. No pristine test.'),indent=2))
