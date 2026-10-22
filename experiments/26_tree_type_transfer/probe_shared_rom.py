"""Shared A-only reduced-order model: four train exposures, two existing validation exposures."""
import json,numpy as np
from build import ROOT
from model_data import observation
cs=[c for c in json.loads((ROOT/'cases.json').read_text()) if c['family']=='single' and c['trees'][0]['type']=='A'];ds=[]
for c in cs:
 d=observation(c);s=d['state'].numpy();n=s.shape[1];tt=np.arange(0,182,2);y=np.column_stack([np.interp(tt,d['time'],s[:,j,k]) for k in range(2) for j in range(n)]);initial=np.r_[np.zeros(n),np.ones(n)];ds.append((c,y-initial,np.array([c['strength'] if t+1<c['duration'] else 0 for t in tt[:-1]])))
train=[d for d in ds if d[0]['split']=='train'];_,_,v=np.linalg.svd(np.concatenate([d[1] for d in train]),full_matrices=False);reports=[]
for rank in [2,4,8,12]:
 basis=v[:rank].T
 for delay in [1,2,4]:
  features=[];targets=[]
  for c,y,h in train:
   z=y@basis
   for j in range(90):features.append(np.r_[np.concatenate([z[max(0,j-k)] for k in range(delay)]),h[j],1]);targets.append(z[j+1])
  X=np.array(features);Y=np.array(targets)
  for ridge in [1e-3,.1,1]:
   operator=np.linalg.solve(X.T@X+ridge*np.eye(X.shape[1]),X.T@Y);rr=[]
   for c,y,h in ds:
    z=[np.zeros(rank)]
    for j in range(90):z.append(np.r_[np.concatenate([z[max(0,j-k)] for k in range(delay)]),h[j],1]@operator)
    p=np.array(z)@basis.T;rr.append(dict(case=c['case'],split=c['split'],temperature_MAE_C=float(abs(p[:,:n]-y[:,:n]).mean()*1000),mass_fraction_MAE=float(abs(p[:,n:]-y[:,n:]).mean())))
   score=float(np.mean([r['temperature_MAE_C']/1000+r['mass_fraction_MAE'] for r in rr if r['split']=='validation']))
   reports.append(dict(rank=rank,delay=delay,ridge=ridge,validation_score=score,rows=rr))
best=min(reports,key=lambda x:x['validation_score']);(ROOT/'results/shared-rom-probe.json').write_text(json.dumps(dict(best=best,candidates=reports,scope='A only; existing development exposures; no test use. No physical bounds imposed. Training-only basis and operators. Initial T20C and mass1; no FDS feedback.'),indent=2));print(json.dumps(best,indent=2))
