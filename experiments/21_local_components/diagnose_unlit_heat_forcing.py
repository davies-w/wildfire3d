"""Post-test surrogate pathway intervention. Not a replacement for frozen predictions."""
import json,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'data/component_frozen'))
import component_hot_state_model as hot
import component_heat_rule as exchange
from component_model import geometry
from component_occlusion import apply
from evaluate_recursive_canopy_energy_budget import rollout
from component_metrics import metrics
frozen=ROOT/'data/component_frozen';model=json.loads((frozen/'model.json').read_text());original=hot.features;original_heat=exchange.predict
rows=[]
for c in json.loads((frozen/'test-inputs.json').read_text())['cases']:
 g=apply(geometry(c,c['extra_surface_patches']),c)
 def modified(g,s,h,t):
  x=original(g,s,h,t);unlit=np.array([n['kind']=='vegetation' and not n['initialized'] for n in g['nodes']]);x[unlit,8:11]=0;return x
 ref=hot.series(json.loads((ROOT/'data/component_test_states'/f"{c['case']}.json").read_text()))
 def measured_heat(model,g,state,t):
  h=original_heat(model,g,state,t)
  for i,n in enumerate(g['nodes']):
   if n['kind']=='vegetation' and not n['initialized']:
    for q in range(2):h[i,q]=np.interp(t,ref['time'],ref['heat'][:,i,q])
  return h
 hot.features=modified;exchange.predict=measured_heat
 r=rollout(model,g,c['horizon_s']);hot.features=original;exchange.predict=original_heat
 ref=hot.series(json.loads((ROOT/'data/component_test_states'/f"{c['case']}.json").read_text()));nt=len(ref['time']);fuels=[]
 for i,n in enumerate(g['nodes']):
  if n['kind']=='vegetation':fuels.append(dict(id=n['id'],initialized=n['initialized'],diagnostic_fuel_kg=float(np.trapezoid(r['state'][:nt,i,3],ref['time'])/17425),FDS_fuel_kg=float(np.trapezoid(ref['state'][:,i,3],ref['time'])/17425)))
 met=metrics(ref,r,g);rows.append(dict(case=c['case'],canopies=fuels,temperature_MAE_C=met['temperature_MAE_all_C'],dose_MAE_kj_m2=met['absolute_dose_MAE_all_kj_m2'],predicted_ignition=met['predicted_ignition']))
out=dict(intervention='Provide measured FDS incoming heat histories only to uninitialized canopy nodes, and zero their three explicit direct-source features. Keep all fitted weights and source/building dynamics. This is deliberately NOT autonomous inference; frozen predictions unchanged.',results=rows,scope='Post-test code-path diagnosis, not held-out validation or a selected improved model. Measured signed convection depends on the FDS surface state. Applying it to a different predicted temperature breaks cooling feedback; this intervention is confounded and cannot isolate transition error from heat-feedback error. Any revised model needs independent testing.')
(ROOT/'results/unlit-measured-heat-diagnosis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
