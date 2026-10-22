"""Compact shared canopy dynamics with explicit heated-mass fractions.
Hybrid: learned local vegetation transitions/heat exchange + known-material wall.
"""
import json
import numpy as np
import component_model as old
import component_heat_rule as exchange
from component_release_rule import wet_mass,HOC
from diagnose_wall_response import advance,surface_temperature
DT=.5

def series(raw):
 c=old.series(raw);pt=np.array([f['time_s'] for f in raw['particle_frames']]);c['state']=np.concatenate([c['state'],np.zeros((*c['state'].shape[:2],2))],axis=2)
 for i in range(len(raw['configuration']['canopies'])):
  values=[]
  for f in raw['particle_frames']:
   a=f['canopies'][i]['classes'];mass=sum(v['represented_mass_kg'] for v in a)
   values.append([max(v['temperature_max_C'] for v in a),sum(v['mass_above300_kg'] for v in a)/max(mass,1e-9),sum(v['mass_above500_kg'] for v in a)/max(mass,1e-9)])
  a=np.array(values)
  for j,index in enumerate([1,4,5]):c['state'][:,i,index]=np.interp(c['time'],pt,a[:,j])
 return c

def features(g,s,h,t):
 pulse=max(0,min(t/.1,1)) if t<=20 else max(0,1-(t-20)/.1)
 src=g['source_kernel']*pulse
 active=(s[:,0]-20)/500
 return np.column_stack([active,(s[:,1]-20)/1500,s[:,2]-1,np.sqrt(np.maximum(s[:,3],0))/300,s[:,4],s[:,5],np.arcsinh(h[:,0]/10),np.arcsinh(h[:,1]/10),src,src*g['wind_speed']/4,src*g['moisture'],active*g['moisture'],s[:,4]*s[:,2],s[:,5]*s[:,2]])

def fit(cases,alpha=100,interaction=True):
 model=exchange.fit({},cases);x=[];y=[];weight=[]
 for c in cases:
  v=np.array([n['kind']=='vegetation' for n in c['g']['nodes']]);st=c['state']
  for k,t in enumerate(c['time'][:-1]):
   f=features(c['g'],st[k],c['heat'][k],t)
   if not interaction:f[:,-2:]=0
   target=(st[k+1]-st[k])/DT;target[:,3]=np.sqrt(np.maximum(st[k+1,:,3],0))/300
   x.extend(f[v]);y.extend(target[v]);weight.extend([1/(v.sum()*(len(st)-1))]*v.sum())
 model.update(vegetation=old.fit_zero_ridge(x,y,weight,alpha),alpha=alpha,interaction=interaction,training_cases=[c['case'] for c in cases],state=['mean_temperature_C','maximum_particle_temperature_C','remaining_wet_mass_fraction','emission_kw','mass_fraction_above300C','mass_fraction_above500C'],scope='Learned recursive vegetation transitions and heat exchange, physical20mm wood wall. Heated fractions are not species-validated. Maximum T may be noisy. One positive uninitialized-canopy training example.')
 return model

def rollout(model,g,horizon=90):
 types=np.array([n['kind'] for n in g['nodes']]);v=types=='vegetation';b=~v;n=len(v);s=np.tile([20.,20.,1.,0.,0.,0.],(n,1));p=np.full((b.sum(),20),20.);initial=wet_mass(g);ignited=np.full(n,np.nan);states=[s.copy()];heats=[];clamps=0;times=np.arange(0,horizon+1e-6,DT)
 for t in times[:-1]:
  h=exchange.predict(model,g,s,t);f=features(g,s,h,t)
  if not model['interaction']:f[:,-2:]=0
  y=old.predict(model['vegetation'],f[v]);nxt=s.copy();nxt[v]+=DT*y;nxt[v,3]=np.maximum(y[:,3],0)**2*90000
  before=nxt.copy();nxt[v,0:2]=np.clip(nxt[v,0:2],20,2500);nxt[v,1]=np.maximum(nxt[v,1],nxt[v,0]);nxt[v,4:6]=np.clip(nxt[v,4:6],0,1);nxt[v,5]=np.minimum(nxt[v,5],nxt[v,4]);nxt[v,2]=np.minimum(s[v,2],np.clip(nxt[v,2],0,1))
  # Total emitted energy cannot exceed remaining represented wet mass times HOC.
  # Wet mass includes moisture: this is only a conservative bound, not dry-fuel chemistry.
  nxt[v,3]=np.minimum(nxt[v,3],s[v,2]*initial[v]*HOC/DT)
  nxt[v,2]=np.minimum(nxt[v,2],np.maximum(0,s[v,2]-nxt[v,3]*DT/(initial[v]*HOC)))
  ambient=5.670374419e-11*293.15**4;p=advance(p,h[b,0],h[b,1],ambient);nxt[b,0]=surface_temperature(p,h[b,0],h[b,1],ambient);nxt[b,1]=s[b,1]+(1-np.exp(-DT/20))*(s[b,0]-s[b,1]);nxt[b,2]=1
  new=b&np.isnan(ignited)&(nxt[:,0]>=350);ignited[new]=t+DT;nxt[b,3]=np.where(np.isnan(ignited[b]),0,200*(1-np.exp(-np.maximum(0,t+DT-ignited[b]))));clamps+=np.count_nonzero(nxt[v]!=before[v]);s=nxt;states.append(s.copy());heats.append(h)
 return dict(time=times,state=np.array(states),heat=np.array(heats),clipped_values=int(clamps))
