"""Expose physically implausible cold pockets; does not modify frozen model."""
import json
import numpy as np
import torch
from original_cnn import ROOT,CNN,prediction,load
cs=json.loads((ROOT/'cases.json').read_text());rows=[]
for name in ['original','physical']:
 m=CNN().to('mps');m.load_state_dict(torch.load(ROOT/f'data/models/{name}.pt',map_location='mps',weights_only=True))
 for c in [c for c in cs if c['split']=='validation']:
  a,t=load(c);b=prediction(m,c,t);temp=b[:,0];ix=np.unravel_index(temp.argmin(),temp.shape)
  rows.append(dict(model=name,case=c['case'],split='validation',minimum_C=float(temp.min()),truth_minimum_C=float(a[:,0].min()),fraction_cells_times_below_zero=float((temp<0).mean()),fraction_below_15C=float((temp<15).mean()),minimum_location_time_index=list(map(int,ix)),FDS_temperature_at_CNN_minimum=float(a[ix[0],0,ix[1],ix[2],ix[3]])))
for c in [c for c in cs if c['split']=='test']:
 a=np.load(ROOT/f"data/test-fields/{c['case']}.npy",mmap_mode='r')
 for name in ['original','physical']:
  b=np.load(ROOT/f"data/predictions/{name}_{c['case']}.npy",mmap_mode='r');temp=b[:,0];rows.append(dict(model=name,case=c['case'],split='fresh_test',minimum_C=float(temp.min()),truth_minimum_C=float(a[:,0].min()),fraction_cells_times_below_zero=float((temp<0).mean()),fraction_below_15C=float((temp<15).mean())))
(ROOT/'results/cold-diagnosis.json').write_text(json.dumps(dict(rows=rows,note='Temperature head is unconstrained. Loss-only repair worsens cold undershoot in development as well as test. Frozen forecasts are retained; no clipping applied to reported errors. A future candidate should bound/penalize background temperature using development evidence and undergo new evaluation.'),indent=2));print(json.dumps(rows,indent=2))
