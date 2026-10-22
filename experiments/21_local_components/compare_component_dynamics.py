"""Development replay diagnostics, without loading configuration validation or test outputs."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import component_model as model
ROOT=Path(__file__).resolve().parent
names=['b21_single_1','b21_transfer_0','b21_single_2','b21_combined_0']
cases=[model.series(json.loads((ROOT/'data/component_states'/f'{n}.json').read_text())) for n in names]
assert all(c['split']=='train' for c in cases)
rows=[]
for transform in ['log','sqrt','linear']:
 for alpha in [10,100,1000]:
  m=model.fit(cases,alpha=alpha,equilibrium=True,emission_transform=transform)
  metrics=[]
  for c in cases:
   r=model.rollout(m,c['g'],90);b=np.array([n['kind']=='building' for n in c['g']['nodes']]);pred=r['state'][:len(c['time']),b,0];truth=c['state'][:,b,0]
   metrics.append(dict(case=c['case'],facade_mae_C=float(np.abs(pred-truth).mean()),facade_peak_C=float(pred.max()),fds_facade_peak_C=float(truth.max()),clipped_values=r['clipped_values'],emission_ceiling_hit=bool(np.max(r['state'][:,:,3])>=99999),max_emission_kw=float(np.max(r['state'][:,:,3])),fds_max_emission_kw=float(np.max(c['state'][:,:,3]))))
  row=dict(transform=transform,alpha=alpha,metrics=metrics);rows.append(row);print(transform,alpha,'MAE',round(np.mean([v['facade_mae_C'] for v in metrics]),2),'ceiling',any(v['emission_ceiling_hit'] for v in metrics),flush=True)
(ROOT/'results/component-dynamics-comparison.json').write_text(json.dumps(dict(training_cases=names,scope='In-sample autonomous replay used to diagnose numerical formulation. Not validation, not selected/frozen model. All variants impose ambient equilibrium. Emission encoding is a numerical modelling choice.',source_sha256=hashlib.sha256((ROOT/'component_model.py').read_bytes()).hexdigest(),candidates=rows),indent=2))
