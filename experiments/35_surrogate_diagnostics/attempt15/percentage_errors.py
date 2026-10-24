"""Normalize saved held-out one-step MAE by matching mean absolute true states.
No inference, fitting, threshold selection or data changes.
"""
from pathlib import Path
import json
import numpy as np
R=Path(__file__).resolve().parent
r=json.loads((R/'data/collected/report.json').read_text())
z=np.load(R/'data/sequences.npz');state=z['state'].astype(float);time=z['time'];config=z['configuration']
rows={}
for window in ['full','ignition','post_source_to90','after90']:
 bases=[];errors=[]
 for test in r['tests']:
  f=test['fold'];ids=np.load(R/f'data/collected/fold{f:02}-test-predictions.npz')['case_indices']
  t=time[ids,1:];truth=np.abs(state[ids,1:])
  mask={'full':np.ones_like(t,dtype=bool),'ignition':t<=20,'post_source_to90':(t>20)&(t<=90),'after90':t>90}[window]
  n=mask.sum(1);assert np.all(n>0)
  percase=(truth*mask[:,:,None]).sum(1)/n[:,None]
  base=np.mean([percase[config[ids]==c].mean(0) for c in np.unique(config[ids])],axis=0)
  m=test['metrics']['one_step'];mae=m['physical_MAE_by_feature'] if window=='full' else m['physical_MAE_by_window'][window]
  bases.append(base);errors.append(mae)
 base=np.mean(bases,axis=0);mae=np.mean(errors,axis=0)
 rows[window]={'mean_absolute_true_state':base.tolist(),'MAE':mae.tolist(),'normalized_MAE_percent':(100*mae/base).tolist()}
out={'definition':'100 * configuration-balanced MAE / configuration-balanced mean absolute true next-state value. Ratio of means, not mean per-point percentage; zero release states retained. Each of ten folds has 48 configurations; replicas averaged first. One-step predictions use observed past history. Not error relative to the state increment.','features':['water_kg','dry_fuel_kg','fuel_gas_release_kg_s'],'windows':rows}
(R/'results/percentage-errors.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
