"""Post-test diagnostic: quantify diffuse predicted HRR; do not refit any model."""
import json,hashlib
import numpy as np,torch
from cnn import ROOT,CNN,load,prediction
f=json.loads((ROOT/'results/prediction-freeze.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
rows=[];m=CNN();m.load_state_dict(torch.load(ROOT/'data/models/cnn_32.pt',map_location='cpu',weights_only=True));m.eval()
cases=json.loads((ROOT/'cases.json').read_text())
for c in [c for c in cases if c['split']=='test']+[c for c in cases if c['split']=='train'][:4]:
 a,t=load(c);wanted=np.array([60.,120.,180.]);idx=abs(t[:,None]-wanted).argmin(0);a=np.array(a[idx]);b=prediction(m,c,t[idx])
 h=np.maximum(b[:,1],0);total=h.sum(axis=(1,2,3))
 rows.append(dict(case=c['case'],split=c['split'],times_s=t[idx].tolist(),FDS_HRR_kW=(np.maximum(a[:,1],0).sum(axis=(1,2,3))*.125).tolist(),CNN_HRR_kW=(total*.125).tolist(),CNN_fraction_HRR_in_cells_below_1_kW_m3=((h*(h<1)).sum(axis=(1,2,3))/np.maximum(total,1e-9)).tolist(),CNN_fraction_HRR_in_gas_below_50C=((h*(b[:,0]<50)).sum(axis=(1,2,3))/np.maximum(total,1e-9)).tolist()))
r=dict(cases=rows,scope='Diagnostic after primary held-out evaluation; frozen model unchanged. Four training cases check whether diffuse late heat release also occurs on fitted examples. This is not a new model test.')
(ROOT/'results/background-diagnosis.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
