"""Fit on named development configurations; select using disjoint validation only."""
import hashlib,json,time
import numpy as np
from scene import ROOT
import component_model as m
TRAIN=['b21_single_1','b21_single_2','b21_transfer_0','b21_transfer_hot','b21_combined_0','b21_corner_1','b21_combined_1']
VALID=['b21_single_validation','b21_transfer_validation']
def load(name):return m.series(json.loads((ROOT/'data/component_states'/f'{name}.json').read_text()))
train=[load(n) for n in TRAIN];valid=[load(n) for n in VALID];assert all(c['split']=='train' for c in train);assert all(c['split']=='validation' for c in valid)
folder=ROOT/'data/component_hybrid_candidates';folder.mkdir(exist_ok=True);records=[]
for interaction in [False,True]:
 for alpha in [10,100,1000]:
  model=m.fit(train,alpha=alpha,interaction=interaction,equilibrium=True,emission_transform='sqrt');model['physical_wall']=True;name=f"hybrid_{'interaction' if interaction else 'additive'}_sqrt_{alpha}";path=folder/(name+'.json');path.write_text(json.dumps(model));metrics=[]
  for c in valid:
   start=time.perf_counter();r=m.rollout(model,c['g'],90);elapsed=time.perf_counter()-start; b=np.array([n['kind']=='building' for n in c['g']['nodes']]);p=r['state'][:len(c['time']),b,0];actual=c['state'][:,b,0];ix=np.flatnonzero(np.max(p,axis=1)>=350);iy=np.flatnonzero(np.max(actual,axis=1)>=350)
   metrics.append(dict(case=c['case'],temperature_MAE_C=float(abs(p-actual).mean()),predicted_peak_C=float(p.max()),reference_peak_C=float(actual.max()),predicted_ignition_s=float(c['time'][ix[0]]) if len(ix) else None,reference_ignition_s=float(c['time'][iy[0]]) if len(iy) else None,clipped_values=r['clipped_values'],emission_ceiling_hit=bool(np.max(r['state'][:,:,3])>=99999),rollout_seconds=elapsed))
  rec=dict(candidate=name,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),fitted_coefficient_count=sum(np.array(v['coef']).size for h in model['models'].values() for v in h.values()),validation=metrics);records.append(rec);print(name,metrics,flush=True)
(ROOT/'results/component-hybrid-validation.json').write_text(json.dumps(dict(training_cases=TRAIN,validation_cases=VALID,candidates=records,scope='Model selection on two whole held-out local configurations, not final Stage C evaluation. Candidate coefficients are stored, not frozen as final. Time rows are correlated; seven training scenes do not provide broad coverage. First ignition uses resampled surface temperature350C; raw boundary audits remain authoritative.'),indent=2))
