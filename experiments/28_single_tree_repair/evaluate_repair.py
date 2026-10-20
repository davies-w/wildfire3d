import json,hashlib
import numpy as np
from pathlib import Path
R=Path(__file__).parent
f=json.loads((R/'results/prediction-freeze.json').read_text());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
rows=[]
for c in json.loads((R/'cases.json').read_text()):
 if c['split']!='test':continue
 a0=np.load(R/f"data/test-fields/{c['case']}.npy",mmap_mode='r');times=np.load(R/f"data/test-fields/{c['case']}-time.npy");t=np.arange(0,181,2);ix=abs(times[:,None]-t).argmin(0);assert max(abs(times[ix]-t))<.3;a=np.array(a0[ix]);ambient=a[0,5]
 for name in ['original','physical','interpolation']:
  b=np.load(R/f"data/predictions/{name}_{c['case']}.npy");metrics={}
  for window,sel in [('all',t>=0),('post_source',t>=22),('late',t>=120)]:
   x=a[sel];y=b[sel];qx=x[:,1].sum((1,2,3))*.125;qy=y[:,1].sum((1,2,3))*.125;hot=(x[:,0]>50)|(y[:,0]>50);rdx=np.maximum(x[:,5]-ambient,0).sum(0);rdy=np.maximum(y[:,5]-ambient,0).sum(0)
   flame_x=x[:,1]>10;flame_y=y[:,1]>10;union=flame_x|flame_y
   metrics[window]=dict(flame_proxy_IoU=float((flame_x&flame_y).sum()/union.sum()) if union.any() else None,velocity_vector_MAE_m_s=float(np.sqrt(((x[:,2:5]-y[:,2:5])**2).sum(1)).mean()),minimum_predicted_temperature_C=float(y[:,0].min()),hot_MAE_C=float(abs(x[:,0]-y[:,0])[hot].mean()) if hot.any() else 0,truth_mean_HRR_kW=float(qx.mean()),predicted_mean_HRR_kW=float(qy.mean()),HRR_curve_relative_L1=float(abs(qx-qy).sum()/max(qx.sum(),1e-8)),radiation_dose_relative_L1=float(abs(rdx-rdy).sum()/max(rdx.sum(),1e-8)),truth_peak_C=float(x[:,0].max()),predicted_peak_C=float(y[:,0].max()))
  rows.append(dict(case=c['case'],model=name,**metrics))
(R/'results/test-summary.json').write_text(json.dumps(dict(freeze_verified=True,rows=rows),indent=2));print(json.dumps(rows,indent=2))
