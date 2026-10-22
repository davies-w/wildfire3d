"""Separate unsupported dynamics from empty-region bookkeeping artifacts."""
import json,numpy as np
from build import ROOT
from model_data import observation,geometry
cases=json.loads((ROOT/'cases.json').read_text());rows=[]
for c in cases:
 if c['family']!='single' or c['split']!='train':continue
 d=observation(c);s=d['state'].numpy();q=d['heat'].numpy();a=np.load(ROOT/'data/extracted'/(c['case']+'.npz'));raw=a['state'].reshape(len(a['time']),-1,6)[:,d['indices']]
 dt=np.diff(d['time']);cap=dt[:,None]*.25*np.clip(abs(s[:-1,:,0])+(np.maximum(q[:-1,:,0]-.4187,0)+np.maximum(q[:-1,:,1],0))/100,0,2);bad=abs(np.diff(s[:,:,0],axis=0))>cap+1e-6;occupied=(raw[:-1,:,5]>0)&(raw[1:,:,5]>0)
 rows.append(dict(case=c['case'],min_observed_C=float(raw[:,:,0].min()),empty_temperature_samples=int((raw[:,:,5]==0).sum()),bound_violations_with_particles_both_sides=int((bad&occupied).sum()),bound_violations_involving_empty_region=int((bad&~occupied).sum())))
(ROOT/'results/target-convention-audit.json').write_text(json.dumps(rows,indent=2))
for r in rows:
 if r['case'].endswith('_1'):print(r)
