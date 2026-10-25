"""Frozen v1 equal-fold summaries from saved test metrics; no fitting."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
r=json.loads((R/'data/collected/report.json').read_text())
out={'scope':'Saved test metrics, within-fold configuration balancing, equal eligible folds; v1 definitions unchanged. Near-zero denominators make quiet percentages unstable.','features':['Water kg','Dry fuel kg','Fuel-gas release kg/s','Surface-heating index K'],'horizons':{},'rollout':{}}
for h in [1,4,8,16,45]:
 out['horizons'][str(h*2)]={}
 for phase in ['v1_active','v1_quiet','v1_weak','v1_transition']:
  arms={}
  for kind in ['control','gated']:
   hs=[t['horizons'][str(h)] for t in r['tests'] if t['kind']==kind]
   eligible=[x for x in hs if x['model_windows'][phase] is not None and x['no_change_windows'][phase] is not None and x['truth_windows'][phase] is not None]
   if not eligible:arms[kind]=None;continue
   m,b,d=[np.mean([x[key][phase] for x in eligible],axis=0) for key in ['model_windows','no_change_windows','truth_windows']]
   arms[kind]=dict(folds=len(eligible),MAE=m.tolist(),no_change_MAE=b.tolist(),mean_absolute_truth=d.tolist(),error_vs_sim_percent=[float(100*x/y) if y else None for x,y in zip(m,d)],improvement_vs_no_change_percent=[float(100*(1-x/y)) if y else None for x,y in zip(m,b)])
  out['horizons'][str(h*2)][phase]=arms
for kind in ['control','gated']:
 rows=[t['metrics']['rollout'] for t in r['tests'] if t['kind']==kind]
 keys=['physical_MAE_by_feature','released_fuel_integral_MAE_kg','peak_release_MAE_kg_s','peak_time_MAE_s','negative_magnitude_mean_by_feature','mass_increase_total_kg']
 out['rollout'][kind]={key:np.mean([x[key] for x in rows],axis=0).tolist() for key in keys}
 out['rollout'][kind]['activity']={key:float(np.mean([x['release_activity_v1'][key] for x in rows if x['release_activity_v1'][key] is not None])) for key in ['missed_active_fraction','false_active_fraction']}
(R/'results/scorecard-summary.json').write_text(json.dumps(out,indent=2,allow_nan=False))
print(json.dumps(out['horizons']['16'],indent=2));print(json.dumps(out['rollout'],indent=2))
