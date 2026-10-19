"""Can the chosen CNN fit one actual training trajectory? Capacity diagnostic only."""
import json,time
import numpy as np,torch
from cnn import ROOT,CNN,cond,encode,decode,load,loss,prediction
c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['case']=='s27_train_0');a,t=load(c);torch.manual_seed(27);rng=np.random.default_rng(27);m=CNN();opt=torch.optim.AdamW(m.parameters(),lr=.001);history=[];start=time.monotonic()
for i in range(401):
 ix=rng.integers(1,len(t),size=2);y=torch.from_numpy(encode(a[ix],c['wind_speed']));p=m(torch.from_numpy(cond(c,t[ix])));l=loss(p,y);opt.zero_grad();l.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
 if i%100==0:history.append(dict(step=i,loss=float(l.detach())))
b=prediction(m,c,t);truth=np.array(a);active=(truth[:,0]>50)|(b[:,0]>50)
r=dict(case=c['case'],steps=401,history=history,temperature_MAE_C=float(abs(b[:,0]-truth[:,0]).mean()),hot_temperature_MAE_C=float(abs(b[:,0]-truth[:,0])[active].mean()),elapsed_s=time.monotonic()-start,scope='Fit on this same single trajectory, not validation. Diagnostic model not reused in final fits.')
(ROOT/'results/one-case-probe.json').write_text(json.dumps(r,indent=2));print(r)
