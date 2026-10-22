import json
import numpy as np
from original_cnn import ROOT,load,cond
cs=json.loads((ROOT/'cases.json').read_text());xs=[];ys=[];splits=[];minimum=20.;amb=[]
for c in cs:
 a,t=load(c);x=cond(c,t);q=np.maximum(a[:,1],0).sum((1,2,3))*.125
 xs.append(x);ys.append(np.log1p(q));splits.extend([c['split']]*len(t))
 if c['split']=='train':minimum=min(minimum,float(a[:,0].min()));amb.append(np.array(a[0,5]))
floor=float(np.floor(minimum)-2);np.savez(ROOT/'data/scalar_targets.npz',x=np.concatenate(xs),logq=np.concatenate(ys),split=np.array(splits))
np.save(ROOT/'data/ambient_radiation.npy',np.mean(amb,axis=0))
(ROOT/'results/temperature-bound.json').write_text(json.dumps(dict(training_minimum_C=minimum,floor_C=floor,rule='Floor is floor(minimum training FDS gas temperature)-2C. Derived only from32 training configurations; fixed setup constraint, not universal material physics.',ambient_C=20),indent=2));print('Training minimum',minimum,'chosen floor',floor,flush=True)
