"""Development-only autonomous rollout and source-free equilibrium regression.
No held-out scene outputs are loaded; these are not validation scores.
"""
import copy,json,time,hashlib
from pathlib import Path
import numpy as np
import component_model as model
ROOT=Path(__file__).resolve().parent
names=['b21_single_1','b21_transfer_0']
cases=[model.series(json.loads((ROOT/'data/component_states'/f'{n}.json').read_text())) for n in names]
rows=[]
for equilibrium in [False,True]:
 m=model.fit(cases,alpha=100,interaction=True,equilibrium=equilibrium)
 for case in cases:
  for source_on in [False,True]:
   g=copy.deepcopy(case['g'])
   if not source_on:g['source_kernel'][:]=0
   start=time.perf_counter();r=model.rollout(m,g,90);elapsed=time.perf_counter()-start
   b=np.array([n['kind']=='building' for n in g['nodes']]);pred=r['state'][:len(case['time']),b,0];truth=case['state'][:,b,0]
   rows.append(dict(case=case['case'],equilibrium_constraint=equilibrium,artificial_source_enabled=source_on,wall_seconds=elapsed,clipped_values=r['clipped_values'],max_building_temperature_C=float(pred.max()),max_all_temperature_C=float(r['state'][:,:,:2].max()),max_emitted_kw=float(r['state'][:,:,3].max()),building_temperature_MAE_C=float(abs(pred-truth).mean()) if source_on else None,cold_fixed_point_pass=bool(np.array_equal(r['state'],np.broadcast_to([20.,20.,1.,0.],r['state'].shape))) if not source_on else None))
   if equilibrium and not source_on:assert rows[-1]['cold_fixed_point_pass']
out=dict(scope='Two development configurations only; autonomous replay diagnostics, not held-out validation. Equilibrium constraint is imposed physical structure, not a learned finding. No final model selected.',model_source_sha256=hashlib.sha256((ROOT/'component_model.py').read_bytes()).hexdigest(),results=rows)
(ROOT/'results/component-rollout-diagnosis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
