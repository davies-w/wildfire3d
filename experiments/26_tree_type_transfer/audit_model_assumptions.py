"""Training-only structural audit and small reduced-order system-identification probe."""
import json,hashlib
import numpy as np
from build import ROOT
from model_data import observation
freeze=json.loads((ROOT/'results/prediction-freeze.json').read_text())
for f,h in freeze['files'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
cases=[c for c in json.loads((ROOT/'cases.json').read_text()) if c['family']=='single' and c['split']=='train'];audits=[];roms=[]
out=ROOT/'data/assumption-audit';out.mkdir(exist_ok=True)
for c in cases:
 d=observation(c);state=d['state'].numpy();heat=d['heat'].numpy();dt=np.diff(d['time']);activity=np.clip(abs(state[:-1,:,0])+(np.maximum(heat[:-1,:,0]-.4187,0)+np.maximum(heat[:-1,:,1],0))/100,0,2)
 bound=dt[:,None]*.25*activity;delta=abs(np.diff(state[:,:,0],axis=0));excess=np.maximum(delta-bound,0)
 audits.append(dict(case=c['case'],oracle_heat_temperature_bound_violations=int((excess>1e-6).sum()),temperature_steps=int(delta.size),largest_impossible_step_C=float(excess.max()*1000),below_model_floor_count=int((state[:,:,0]<-1e-6).sum()),mass_increase_steps=int((np.diff(state[:,:,1],axis=0)>1e-5).sum())))
 if not c['case'].endswith('_1'):continue
 # Reconstruct known single-case trajectories only. Same data for fitting and scoring: NOT transfer evidence.
 tt=np.arange(0,182,2);n=state.shape[1];y=np.column_stack([np.interp(tt,d['time'],state[:,j,k]) for k in range(2) for j in range(n)])
 initial=y[0].copy();center=y-initial;u,s,v=np.linalg.svd(center,full_matrices=False);heater=np.array([c['strength'] if t+1<c['duration'] else 0 for t in tt[:-1]])
 records=[];best=None
 for rank in [2,4,8,12]:
  basis=v[:rank].T;z=center@basis
  for delay in [1,2,4]:
   features=np.array([np.r_[np.concatenate([z[max(0,j-k)] for k in range(delay)]),heater[j],1] for j in range(len(z)-1)])
   for ridge in [1e-6,1e-3,.1]:
    reg=np.eye(features.shape[1])*ridge;coef=np.linalg.solve(features.T@features+reg,features.T@z[1:]);pred=[z[0]]
    for j in range(len(z)-1):pred.append(np.r_[np.concatenate([pred[max(0,j-k)] for k in range(delay)]),heater[j],1]@coef)
    predicted=np.array(pred)@basis.T+initial
    terr=float(abs(predicted[:,:n]-y[:,:n]).mean()*1000);merr=float(abs(predicted[:,n:]-y[:,n:]).mean());score=terr/1000+merr
    record=dict(rank=rank,delay=delay,ridge=ridge,temperature_MAE_C=terr,mass_fraction_MAE=merr,dynamic_coefficients=int(coef.size),basis_coefficients=int(basis.size),fraction_outside_0_1=int(((predicted[:,n:]<0)|(predicted[:,n:]>1)).sum()))
    records.append(record)
    if np.isfinite(score) and (best is None or score<best[0]):best=(score,record,predicted,basis,coef)
 np.savez_compressed(out/(c['case']+'-rom.npz'),time=tt,truth=y,prediction=best[2],basis=best[3],operator=best[4],initial=initial)
 roms.append(dict(case=c['case'],best=best[1],candidates=records,selection='Selected by same-trajectory autonomous reconstruction error, not validation; basis fit to entire same trajectory; initial snapshot supplied, no subsequent FDS feedback. No generalization claim.'))
 print(c['case'],audits[-1],roms[-1]['best'] if c['case'].endswith('_1') else '',flush=True)
(ROOT/'results/model-assumption-audit.json').write_text(json.dumps(dict(structural=audits,reduced_order=roms,original_hashes_verified=len(freeze['files'])),indent=2))
