"""Post-test surrogate pathway intervention. Not a replacement for frozen predictions."""
import json,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'data/component_frozen'))
import component_hot_state_model as hot
from component_model import geometry
from component_occlusion import apply
from evaluate_recursive_canopy_energy_budget import rollout
from component_metrics import metrics
frozen=ROOT/'data/component_frozen';model=json.loads((frozen/'model.json').read_text());original=hot.features
rows=[]
for c in json.loads((frozen/'test-inputs.json').read_text())['cases']:
 g=apply(geometry(c,c['extra_surface_patches']),c)
 def modified(g,s,h,t):
  x=original(g,s,h,t);unlit=np.array([n['kind']=='vegetation' and not n['initialized'] for n in g['nodes']]);x[unlit,8:11]=0;return x
 hot.features=modified
 r=rollout(model,g,c['horizon_s']);hot.features=original
 ref=hot.series(json.loads((ROOT/'data/component_test_states'/f"{c['case']}.json").read_text()));nt=len(ref['time']);fuels=[]
 for i,n in enumerate(g['nodes']):
  if n['kind']=='vegetation':fuels.append(dict(id=n['id'],initialized=n['initialized'],diagnostic_fuel_kg=float(np.trapezoid(r['state'][:nt,i,3],ref['time'])/17425),FDS_fuel_kg=float(np.trapezoid(ref['state'][:,i,3],ref['time'])/17425)))
 met=metrics(ref,r,g);rows.append(dict(case=c['case'],canopies=fuels,temperature_MAE_C=met['temperature_MAE_all_C'],dose_MAE_kj_m2=met['absolute_dose_MAE_all_kj_m2'],predicted_ignition=met['predicted_ignition']))
out=dict(intervention='Only zero three explicit direct-source network features on non-initialized canopies. Keep source contribution to predicted incident heat, neighbour transport, all fitted weights and source-canopy features. Frozen predictions unchanged.',results=rows,scope='Post-test code-path diagnosis, not held-out validation or a selected improved model. Any revised model needs independent testing; intervention may harm real externally ignited receivers.')
(ROOT/'results/direct-source-pathway-diagnosis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
