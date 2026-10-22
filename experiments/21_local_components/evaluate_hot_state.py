import json,time,hashlib
import numpy as np
from scene import ROOT
import component_hot_state_model as m
TRAIN=['b21_single_1','b21_single_2','b21_transfer_0','b21_transfer_hot','b21_combined_0','b21_corner_1','b21_combined_1'];VALID=['b21_single_validation','b21_transfer_validation']
load=lambda n:m.series(json.loads((ROOT/'data/component_states'/f'{n}.json').read_text()))
train=[load(n) for n in TRAIN];valid=[load(n) for n in VALID];assert all(c['split']=='train' for c in train);assert all(c['split']=='validation' for c in valid)
folder=ROOT/'data/hot_state_candidates';folder.mkdir(exist_ok=True);rows=[]
for interaction in [False,True]:
 for alpha in [1,10,100]:
  model=m.fit(train,alpha,interaction);name=f"hot_{'interaction' if interaction else 'independent'}_{alpha}";p=folder/(name+'.json');p.write_text(json.dumps(model));metrics=[]
  for c in valid:
   start=time.perf_counter();r=m.rollout(model,c['g']);wall=time.perf_counter()-start;b=np.array([n['kind']=='building' for n in c['g']['nodes']]);pred=r['state'][:len(c['time']),b,0];truth=c['state'][:,b,0];ix=np.flatnonzero(pred.max(1)>=350);iy=np.flatnonzero(truth.max(1)>=350)
   metrics.append(dict(case=c['case'],MAE_C=float(abs(pred-truth).mean()),peak_C=float(pred.max()),reference_peak_C=float(truth.max()),ignition_s=float(c['time'][ix[0]]) if len(ix) else None,reference_ignition_s=float(c['time'][iy[0]]) if len(iy) else None,clipped_values=r['clipped_values'],wall_seconds=wall))
  rows.append(dict(candidate=name,model_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),coefficient_count=18+np.array(model['vegetation']['coef']).size,validation=metrics));print(name,metrics,flush=True)
(ROOT/'results/hot-state-validation.json').write_text(json.dumps(dict(training=TRAIN,validation=VALID,candidates=rows,scope='Local validation/model selection only. No Stage C outputs. Compact hybrid with learned heated-mass fractions; not a pure DNN.'),indent=2))
