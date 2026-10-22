"""Local-validation error localization; no held-out FDS reads or refitting."""
import copy,json
from pathlib import Path
import numpy as np
from scene import ROOT
import component_hot_state_model as hot
from component_occlusion import apply
from evaluate_recursive_canopy_energy_budget import rollout
from component_metrics import metrics
m=json.loads((ROOT/'data/component_frozen/model.json').read_text());rows=[]
for name in ['b21_single_validation','b21_transfer_validation','b21_combined_validation','b21_corner_validation']:
 raw=json.loads((ROOT/'data/component_states'/f'{name}.json').read_text());ref=hot.series(raw);g=apply(copy.deepcopy(ref['g']),raw['configuration']);p=rollout(m,g);met=metrics(ref,p,g);groups={}
 for patch in met['per_patch']:
  node=next(n for n in g['nodes'] if n['id']==patch['id']);normal=tuple(node['normal']);key='roof_top' if normal==(0,0,1) else 'roof_underside' if normal==(0,0,-1) else 'wall_'+str(normal);groups.setdefault(key,[]).append(patch)
 summary={}
 for k,ps in groups.items():
  exposed=[x for x in ps if x['exposed']];summary[k]=dict(patches=len(ps),exposed=len(exposed),temperature_MAE_C=float(np.mean([x['temperature_MAE_C'] for x in ps])),median_exposed_dose_error=float(np.median([x['normalized_error'] for x in exposed])) if exposed else None,reference_dose_mean=float(np.mean([x['reference_dose_kj_m2'] for x in ps])),predicted_dose_mean=float(np.mean([x['predicted_dose_kj_m2'] for x in ps])))
 rows.append(dict(case=name,groups=summary))
out=dict(results=rows,interpretation='Local diagnostic only. Static point-emitter/straight-line transport lacks resolved plume geometry, convection and canopy hot-zone locations; these are candidate explanations, not isolated causes. No parameters changed after freeze.')
(ROOT/'results/selected-component-error-breakdown.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
