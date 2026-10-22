"""Shared regularized local transitions + heat messages. No FDS access during rollout.
Vegetation state: mean T, hot-tail T, remaining wet-mass fraction, emitted kW.
Facade state: T, 20s thermal-memory filter, unit mass marker, emitted kW.
The thermal-memory filter is a modelling approximation, not measured internal T.
"""
import json,math
import numpy as np
HOC=17425.
DT=.5

def geometry(c,facade):
 nodes=[]
 for n in c['canopies']:nodes.append(dict(kind='vegetation',id=n['id'],xyz=[n['x'],n['y'],n['base']+n['height']/3],radius=n['radius'],height=n['height'],area=1.,normal=[0,0,0],initialized=n['initialized']))
 for f in facade:nodes.append(dict(kind='building',id=f['id'],xyz=f['xyz'],radius=.5,height=1.,area=f.get('area',1.),normal=f['normal'],initialized=False))
 xyz=np.array([n['xyz'] for n in nodes]);delta=xyz[:,None,:]-xyz[None,:,:];dist2=(delta**2).sum(-1);r=np.array([n['radius'] for n in nodes]);kernel=1/(4*np.pi*(dist2+r[None,:]**2+1));np.fill_diagonal(kernel,0)
 angle=np.deg2rad(c.get('direction',c.get('wind_direction_deg',270)));wind=np.array([-np.sin(angle),-np.cos(angle),0]);aligned=np.maximum(0,np.einsum('ijk,k->ij',delta,wind)/np.sqrt(np.maximum(dist2,1)))
 normal=np.array([n['normal'] for n in nodes]);facing=np.maximum(0,-np.einsum('ijk,ik->ij',delta,normal)/np.sqrt(np.maximum(dist2,1)));facing[:len(c['canopies'])]=1
 kernel*=facing
 sources=[]
 for n in c['canopies']:
  if n['initialized']:sources.append([n['x'],n['y'],n['base']+.1])
 source_delta=xyz[:,None,:]-np.array(sources)[None,:,:] if sources else np.zeros((len(nodes),0,3));source_kernel=(1/(4*np.pi*((source_delta**2).sum(-1)+2.25))).sum(1)
 return dict(nodes=nodes,kernel=kernel,aligned=aligned,source_kernel=source_kernel,wind_speed=c.get('wind_m_s',c.get('wind_speed_m_s',3)),moisture=c['moisture'])

def series(raw):
 c=raw['configuration'];g=geometry(c,raw['facade']);times=np.arange(0,min(raw['particle_frames'][-1]['time_s'],raw['facade'][0]['time_s'][-1])+1e-5,DT);nv=len(c['canopies']);states=np.zeros((len(times),len(g['nodes']),4));heat=np.zeros((len(times),len(g['nodes']),2));pt=np.array([f['time_s'] for f in raw['particle_frames']])
 for i in range(nv):
  vals=[];heats=[]
  for frame in raw['particle_frames']:
   n=frame['canopies'][i];a=n['classes'];m=np.array([v['represented_mass_kg'] for v in a]);area=np.array([v['represented_area_m2'] for v in a]);mass=m.sum();den=max(mass,1e-9);aden=max(area.sum(),1e-9)
   vals.append([sum(v['temperature_mass_mean_C']*w for v,w in zip(a,m))/den if mass else 20,max(v['temperature_p95_C'] for v in a),mass,n['fuel_release_kg_s']*HOC]);heats.append([sum(v['incident_radiation_area_mean_kw_m2']*w for v,w in zip(a,area))/aden,sum(v['convection_area_mean_kw_m2']*w for v,w in zip(a,area))/aden])
  v=np.array(vals);v[:,2]/=max(v[:,2].max(),1e-9);h=np.array(heats)
  for k in range(4):states[:,i,k]=np.interp(times,pt,v[:,k])
  for k in range(2):heat[:,i,k]=np.interp(times,pt,h[:,k])
 for j,f in enumerate(raw['facade'],nv):
  t=f['time_s'];temp=np.interp(times,t,f['temperature_C']);states[:,j,0]=temp;states[:,j,1]=temp[0];states[:,j,2]=1;states[:,j,3]=np.interp(times,t,f['burning_kg_m2_s'])*HOC
  for k in range(1,len(times)):states[k,j,1]=states[k-1,j,1]+(1-np.exp(-DT/20))*(temp[k-1]-states[k-1,j,1])
  heat[:,j,0]=np.interp(times,t,f['incident_radiation_kw_m2']);heat[:,j,1]=np.interp(times,t,f['convection_kw_m2'])
 # Ambient incoming radiation is retained separately; heat model learns excess above ambient.
 ambient=heat[0,:,0].copy();heat[:,:,0]-=ambient[None,:]
 return dict(case=raw['case'],split=raw['split'],g=g,time=times,state=states,heat=heat,ambient=ambient)

def features(g,state,time,interaction=True):
 n=len(g['nodes']);emission=np.maximum(state[:,3],0)*np.array([v['area'] for v in g['nodes']]);messages=g['kernel']*emission[None,:];rad=messages.sum(1);conv=(messages*g['aligned']).sum(1);pulse=max(0,min(time/.1,1)) if time<=20 else max(0,1-(time-20)/.1)
 # Approximate prescribed-source scale; coefficient is learned, not treated as measured heat input.
 source=g['source_kernel']*1200*pulse
 a=np.array([[v['radius']/3,v['height']/10,v['xyz'][2]/10,float(v['kind']=='building')] for v in g['nodes']]);x=np.column_stack([state[:,0]/500,state[:,1]/500,state[:,2],np.log1p(emission)/10,a,np.full(n,g['wind_speed']/4),np.full(n,g['moisture']),rad/100,conv/100,source/100])
 if interaction:
  pair=(rad**2-(messages**2).sum(1))/2
  x=np.column_stack([x,np.log1p(np.maximum(pair,0))/10,rad*state[:,0]/50000,conv*state[:,2]/100])
 return x

def equilibrium_features(g,state,time,interaction=True):
 # Zero input maps to zero output exactly. Static geometry modulates activity,
 # rather than supplying an intercept that can create heat in an ambient scene.
 cold=np.tile([20.,20.,1.,0.],(len(state),1))
 x=features(g,state,time,interaction);base=features(g,cold,0,interaction)
 delta=x-base
 activity=np.column_stack([(state[:,0]-20)/500,(state[:,1]-20)/500,np.log1p(np.maximum(state[:,3],0))/10,delta[:,12]])
 return np.column_stack([delta,(base[:,:,None]*activity[:,None,:]).reshape(len(state),-1)])

def fit_zero_ridge(x,y,weight,alpha):
 x=np.asarray(x);y=np.asarray(y);w=np.asarray(weight);scale=np.sqrt(np.average(x*x,axis=0,weights=w));scale[scale<1e-8]=1
 z=x/scale;root=np.sqrt(w/w.mean());coef=np.linalg.solve((z*root[:,None]).T@(z*root[:,None])+np.eye(z.shape[1])*alpha,(z*root[:,None]).T@(y*root[:,None]))
 return dict(mean=np.zeros(x.shape[1]).tolist(),scale=scale.tolist(),coef=np.vstack([np.zeros((1,y.shape[1])),coef]).tolist())

def fit_ridge(x,y,weight,alpha):
 x=np.asarray(x);y=np.asarray(y);w=np.asarray(weight);mean=np.average(x,axis=0,weights=w);scale=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));scale[scale<1e-8]=1
 z=np.column_stack([np.ones(len(x)),(x-mean)/scale]);root=np.sqrt(w/w.mean());reg=np.eye(z.shape[1])*alpha;reg[0,0]=0;coef=np.linalg.solve((z*root[:,None]).T@(z*root[:,None])+reg,(z*root[:,None]).T@(y*root[:,None]));return dict(mean=mean.tolist(),scale=scale.tolist(),coef=coef.tolist())
def predict(m,x):return np.column_stack([np.ones(len(x)),(x-np.array(m['mean']))/np.array(m['scale'])])@np.array(m['coef'])

def fit(cases,alpha=10,interaction=True,equilibrium=False,emission_transform="log"):
 assert emission_transform in ["log","sqrt","linear"]
 encode_emission=lambda e: np.log1p(e) if emission_transform=="log" else np.sqrt(e) if emission_transform=="sqrt" else e/1000
 feature_fn=equilibrium_features if equilibrium else features
 fitter=fit_zero_ridge if equilibrium else fit_ridge
 data={kind:dict(x=[],h=[],y=[],w=[]) for kind in ['vegetation','building']}
 for c in cases:
  st=c['state'];g=c['g'];types=np.array([n['kind'] for n in g['nodes']])
  for k,t in enumerate(c['time'][:-1]):
   x=feature_fn(g,st[k],t,interaction);h=c['heat'][k];local=np.column_stack([x,np.arcsinh(h/10)])
   for kind in data:
    mask=types==kind;count=mask.sum()
    if not count:continue
    y=np.column_stack([(st[k+1,:,0]-st[k,:,0])/DT,(st[k+1,:,1]-st[k,:,1])/DT,(st[k+1,:,2]-st[k,:,2])/DT,encode_emission(np.maximum(st[k+1,:,3],0))])
    data[kind]['x'].extend(x[mask]);data[kind]['h'].extend(np.arcsinh(h[mask]/10));data[kind]['y'].extend(np.column_stack([local[mask],y[mask]]));data[kind]['w'].extend([1/((len(st)-1)*count)]*count)
 models={}
 for kind,v in data.items():
  xy=np.array(v['y']);models[kind]=dict(heat=fitter(v['x'],v['h'],v['w'],alpha),transition=fitter(xy[:,:-4],xy[:,-4:],v['w'],alpha))
 return dict(models=models,emission_transform=emission_transform,equilibrium=equilibrium,interaction=interaction,alpha=alpha,dt=DT,training_cases=[c['case'] for c in cases],limitations='Shared ridge surrogate; no conservation guarantee. Vegetation state reduced to2 temperatures,total wet mass fraction,emission.20s facade memory is approximate. Interaction head adds combined-source and receiver-state terms; explicit shielding is not yet represented.')

def rollout(model,g,horizon=90):
 from diagnose_wall_response import advance,surface_temperature
 n=len(g['nodes']);s=np.tile([20.,20.,1.,0.],(n,1));states=[s.copy()];heats=[];times=np.arange(0,horizon+1e-6,DT);types=np.array([n['kind'] for n in g['nodes']]);ignited=np.full(n,np.nan);clamps=0;wall_mask=types=='building';wall_profile=np.full((wall_mask.sum(),20),20.)
 for t in times[:-1]:
  x=(equilibrium_features if model.get('equilibrium') else features)(g,s,t,model['interaction']);h=np.zeros((n,2));y=np.zeros((n,4))
  if 'exchange_heads' in model:
   from component_heat_rule import predict as predict_exchange
   h=predict_exchange(model,g,s,t)
  for kind,head in model['models'].items():
   mask=types==kind
   if 'exchange_heads' not in model:h[mask]=np.sinh(np.clip(predict(head['heat'],x[mask]),-7,7))*10
   y[mask]=predict(head['transition'],np.column_stack([x[mask],np.arcsinh(h[mask]/10)]))
  nxt=s.copy();nxt[:,:3]+=DT*y[:,:3];mode=model.get('emission_transform','log')
  nxt[:,3]=np.expm1(np.clip(y[:,3],0,np.log1p(100000))) if mode=='log' else np.minimum(np.maximum(y[:,3],0)**2,100000) if mode=='sqrt' else np.clip(y[:,3]*1000,0,100000)
  b=types=='building'
  if 'release_coefficients' in model:
   from component_release_rule import predict as predict_release
   nxt[~b,3]=predict_release(model,g,s)[~b]
  if model.get('physical_wall',False):
   ambient=5.670374419e-11*(293.15**4)
   wall_profile=advance(wall_profile,h[b,0],h[b,1],ambient)
   nxt[b,0]=surface_temperature(wall_profile,h[b,0],h[b,1],ambient)
  new=b&np.isnan(ignited)&(nxt[:,0]>=350);ignited[new]=t+DT;nxt[b,1]=s[b,1]+(1-np.exp(-DT/20))*(s[b,0]-s[b,1]);nxt[b,2]=1;nxt[b,3]=np.where(np.isnan(ignited[b]),0,200*(1-np.exp(-np.maximum(0,t+DT-ignited[b]))))
  unclipped=nxt.copy();nxt[:,:2]=np.clip(nxt[:,:2],20,2500);nxt[:,2]=np.minimum(s[:,2],np.clip(nxt[:,2],0,1));clamps+=int(np.count_nonzero(nxt!=unclipped));s=nxt;states.append(s.copy());heats.append(h)
 return dict(time=times,state=np.array(states),heat=np.array(heats),clipped_values=clamps)
