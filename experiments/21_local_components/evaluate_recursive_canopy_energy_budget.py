"""Fully autonomous evaluation of trajectory-trained canopy network."""
import json,sys,time,hashlib
import numpy as np
from scene import ROOT
import component_hot_state_model as hot
from component_release_rule import wet_mass,HOC
from diagnose_wall_response import advance,surface_temperature
import component_heat_rule as exchange

def step(model,g,s,h,t):
 v=np.array([n['kind']=='vegetation' for n in g['nodes']]);x=hot.features(g,s,h,t)[v];power_scale=np.sqrt(wet_mass(g)[v]/(1+g['moisture'])/77) if model.get('power_normalized_by_dry_mass',False) else np.ones(v.sum());x[:,3]/=power_scale;w=model['weights'];a=np.array(w['a.weight']);bias=np.array(w['a.bias']);b=np.array(w['b.weight']);delta=(np.tanh(x@a.T+bias)-np.tanh(bias))@b.T
 st=s[v];z=np.column_stack([(st[:,0]-20)/500,(st[:,1]-20)/1500,1-st[:,2],np.sqrt(np.maximum(st[:,3],0))/300/power_scale,st[:,4],st[:,5]]);prev=z.copy();z=np.minimum(np.maximum(z+.5*delta,0),[5.,1.65,1.,3.,1.,1.]);z[:,2]=np.maximum(prev[:,2],z[:,2]);z[:,1]=np.maximum(z[:,1],z[:,0]/3);z[:,5]=np.minimum(z[:,5],z[:,4])
 return np.column_stack([20+500*z[:,0],20+1500*z[:,1],1-z[:,2],90000*z[:,3]**2*power_scale**2,z[:,4],z[:,5]])

def rollout(model,g,horizon=90):
 v=np.array([n['kind']=='vegetation' for n in g['nodes']]);b=~v;s=np.tile([20.,20.,1.,0.,0.,0.],(len(v),1));p=np.full((b.sum(),20),20.);remaining=wet_mass(g)/(1+g['moisture']);states=[s.copy()];heats=[];times=np.arange(0,horizon+1e-6,.5);ignited=np.full(len(v),np.nan)
 for t in times[:-1]:
  seeded=v&np.array([n['initialized'] for n in g['nodes']])
  if model.get('source_library'):
   from component_additive_baseline import source_power
   s[seeded,3]=np.minimum(source_power(model['source_library'],g,t)[seeded],remaining[seeded]*HOC/.5)
  h=exchange.predict(model,g,s,t);nxt=s.copy();nxt[v]=step(model,g,s,h,t)
  if model.get('source_library'):nxt[seeded,3]=s[seeded,3]
  nxt[v,3]=np.minimum(nxt[v,3],remaining[v]*HOC/.5);remaining[v]=np.maximum(0,remaining[v]-nxt[v,3]*.5/HOC);ambient=5.670374419e-11*293.15**4;p=advance(p,h[b,0],h[b,1],ambient);nxt[b,0]=surface_temperature(p,h[b,0],h[b,1],ambient);nxt[b,1]=s[b,1]+(1-np.exp(-.5/20))*(s[b,0]-s[b,1]);new=b&np.isnan(ignited)&(nxt[:,0]>=350);ignited[new]=t+.5;nxt[b,3]=np.where(np.isnan(ignited[b]),0,200*(1-np.exp(-np.maximum(0,t+.5-ignited[b]))));s=nxt;states.append(s.copy());heats.append(h)
 return dict(state=np.array(states),heat=np.array(heats),time=times)

def main():
 epoch=int(sys.argv[1]);path=ROOT/'data/recursive_canopy_constrained'/f'epoch{epoch}.json';model=json.loads(path.read_text());rows=[]
 for name in ['b21_single_validation','b21_transfer_validation']:
  c=hot.series(json.loads((ROOT/'data/component_states'/f'{name}.json').read_text()));assert c['split']=='validation';start=time.perf_counter();r=rollout(model,c['g']);elapsed=time.perf_counter()-start;b=np.array([n['kind']=='building' for n in c['g']['nodes']]);pred=r['state'][:len(c['time']),b,0];truth=c['state'][:,b,0];ix=np.flatnonzero(pred.max(1)>=350);iy=np.flatnonzero(truth.max(1)>=350);v=~b
  rows.append(dict(case=name,MAE_C=float(abs(pred-truth).mean()),peak_C=float(pred.max()),reference_peak_C=float(truth.max()),ignition_s=float(c['time'][ix[0]]) if len(ix) else None,reference_ignition_s=float(c['time'][iy[0]]) if len(iy) else None,wall_seconds=elapsed,minimum_remaining_mass_fraction=float(r['state'][:,v,2].min()),maximum_hot_fraction=float(r['state'][:,v,4:6].max())))
 out=dict(epoch=epoch,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),validation=rows,scope='Fully autonomous local validation; no FDS states supplied during rollout. Bounded state plus total emitted-fuel budget from geometric dry mass; remaining wet-mass prediction is separate, so detailed chemical/mass consistency is unproven. No Stage C outputs.');(ROOT/'results'/f'recursive-canopy-energy-budget-validation-{epoch}.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
