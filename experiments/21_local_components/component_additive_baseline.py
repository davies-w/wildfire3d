"""Separately fitted additive baseline from single-canopy training configurations.
Interpolated normalized source-emission curves; no canopy-to-canopy ignition.
Neighbour heat contributions add, followed by the same known-material wall response.
"""
import json
import numpy as np
from scene import ROOT
import component_hot_state_model as hot
import component_heat_rule as exchange
from component_release_rule import wet_mass,HOC
from diagnose_wall_response import advance,surface_temperature

def fit():
 manifest=json.loads((ROOT/'component-development.json').read_text());cases=[];curves=[]
 for c in manifest['cases']:
  if c['split']!='train' or c['family']!='single' or not (ROOT/'results'/f"{c['case']}-audit.json").exists():continue
  r=hot.series(json.loads((ROOT/'data/component_states'/f"{c['case']}.json").read_text()));cases.append(r);mass=wet_mass(r['g'])[0]/(1+r['g']['moisture']);curves.append(dict(case=c['case'],wind_m_s=c['wind_m_s'],moisture=c['moisture'],time_s=r['time'].tolist(),power_kw_per_kg=(r['state'][:,0,3]/mass).tolist()))
 assert len(cases)>=3
 model=exchange.fit({},cases);model.update(training_cases=[c['case'] for c in cases],curves=curves,scope='Separate single-canopy-only additive baseline: interpolate normalized source power by wind/moisture, scale by geometric dry fuel mass, sum heat contributions, integrate identical wall response. Uninitialized canopies cannot ignite. Training source curves may include building feedback; not purified free-burning sources. No FDS call during prediction.')
 return model

def source_power(model,g,t):
 conditions=np.array([[c['wind_m_s'],c['moisture']] for c in model['curves']]);scale=np.maximum(np.ptp(conditions,axis=0),[1,.01]);dist=np.sum(((conditions-[g['wind_speed'],g['moisture']])/scale)**2,axis=1)
 if dist.min()<1e-12:w=(dist==dist.min()).astype(float)
 else:w=1/dist
 w/=w.sum();power=sum(v*np.interp(t,c['time_s'],c['power_kw_per_kg']) for v,c in zip(w,model['curves']));dry=wet_mass(g)/(1+g['moisture']);return power*dry*np.array([n['initialized'] for n in g['nodes']])

def rollout(model,g,horizon=90):
 v=np.array([n['kind']=='vegetation' for n in g['nodes']]);b=~v;s=np.tile([20.,20.,1.,0.,0.,0.],(len(v),1));p=np.full((b.sum(),20),20.);remaining=wet_mass(g)/(1+g['moisture']);states=[s.copy()];heats=[];times=np.arange(0,horizon+1e-6,.5);ignited=np.full(len(v),np.nan)
 for t in times[:-1]:
  s[v,3]=np.minimum(source_power(model,g,t)[v],remaining[v]*HOC/.5);h=exchange.predict(model,g,s,t);remaining[v]=np.maximum(0,remaining[v]-s[v,3]*.5/HOC);nxt=s.copy();ambient=5.670374419e-11*293.15**4;p=advance(p,h[b,0],h[b,1],ambient);nxt[b,0]=surface_temperature(p,h[b,0],h[b,1],ambient);nxt[b,1]=s[b,1]+(1-np.exp(-.5/20))*(s[b,0]-s[b,1]);new=b&np.isnan(ignited)&(nxt[:,0]>=350);ignited[new]=t+.5;nxt[b,3]=np.where(np.isnan(ignited[b]),0,200*(1-np.exp(-np.maximum(0,t+.5-ignited[b]))));s=nxt;states.append(s.copy());heats.append(h)
 return dict(state=np.array(states),heat=np.array(heats),time=times)

if __name__=='__main__':
 model=fit();p=ROOT/'data/additive_baseline.json';p.write_text(json.dumps(model));print('Fitted baseline from',model['training_cases'])
