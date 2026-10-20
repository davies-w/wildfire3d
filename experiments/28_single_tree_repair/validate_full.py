"""All validation times, not just training-screen snapshots."""
import json
import numpy as np
import torch
from original_cnn import CNN,prediction,ROOT,load
rows=[]
for name in ['original','physical']:
 m=CNN().to('mps' if torch.backends.mps.is_available() else 'cpu');m.load_state_dict(torch.load(ROOT/f'data/models/{name}.pt',map_location=next(m.parameters()).device,weights_only=True));m.eval()
 for c in json.loads((ROOT/'cases.json').read_text()):
  if c['split']!='validation':continue
  a,t=load(c);b=prediction(m,c,t);sel=t>=22;x=np.array(a[sel]);y=b[sel];hot=(x[:,0]>50)|(y[:,0]>50);q=x[:,1].sum((1,2,3))*.125;qb=y[:,1].sum((1,2,3))*.125;ambient=a[0,5];gx=np.maximum(x[:,5]-ambient,0).sum(0);gy=np.maximum(y[:,5]-ambient,0).sum(0)
  rows.append(dict(model=name,case=c['case'],hot_MAE_C=float(abs(x[:,0]-y[:,0])[hot].mean()),HRR_curve_relative_L1=float(abs(q-qb).sum()/max(q.sum(),1)),radiation_dose_relative_L1=float(abs(gx-gy).sum()/max(gx.sum(),1)),peak_error_C=float(abs(x[:,0].max()-y[:,0].max())),late_mean_kW=float(b[t>=120,1].sum((1,2,3)).mean()*.125)))
  print(name,c['case'],flush=True)
summary={name:{k:float(np.mean([r[k] for r in rows if r['model']==name])) for k in ['hot_MAE_C','HRR_curve_relative_L1','radiation_dose_relative_L1','peak_error_C','late_mean_kW']} for name in ['original','physical']}
a=summary['original'];b=summary['physical'];passed=b['hot_MAE_C']<=1.1*a['hot_MAE_C'] and all(b[k]<a[k] for k in ['HRR_curve_relative_L1','radiation_dose_relative_L1','peak_error_C']) and b['late_mean_kW']<.1*a['late_mean_kW']
(ROOT/'results/full-validation.json').write_text(json.dumps(dict(rows=rows,summary=summary,pass_all=bool(passed)),indent=2));print(json.dumps(summary,indent=2),'PASS',passed)
