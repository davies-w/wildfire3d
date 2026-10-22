"""Development-only true-state heat diagnostic; never used by frozen Stage C model.
Three vertically distributed canopy emitters and separate wind/plume convection features.
This uses measured component states to isolate transport representational error.
"""
import json
import numpy as np
from scipy.optimize import lsq_linear
from scene import ROOT
import component_hot_state_model as hot
import component_heat_rule as exchange
from component_occlusion import apply
from component_occlusion import clear_segments

def kernels(c,g):
 nodes=g['nodes'];xyz=np.array([n['xyz'] for n in nodes]);norm=np.array([n['normal'] for n in nodes]);rad=[]
 boxes=c.get('building_boxes')
 if boxes is None:
  f=c['facade'];boxes=[[f['x'],f['x']+.5,*f['y'],*f['z']]]
  if c.get('family')=='corner':boxes.append([24,30,16,16.5,0,6])
  if c.get('roof_box_m'):boxes.append(c['roof_box_m'])
 for height in [.2,.6,1.]:
  emit=xyz.copy()
  for j,n in enumerate(c['canopies']):emit[j,2]=n['base']+height*n['height']
  delta=xyz[:,None,:]-emit[None,:,:];d2=(delta**2).sum(2);face=np.maximum(0,-np.einsum('ijk,ik->ij',delta,norm)/np.sqrt(np.maximum(d2,1)));face[:len(c['canopies'])]=1
  k=face/(4*np.pi*(d2+np.array([n['radius']**2 for n in nodes])[None,:]+1));np.fill_diagonal(k,0);k*=clear_segments(xyz,emit,boxes);rad.append(k)
 # Distinct plume convection envelope: downwind reach and upward distance,
 # not gated by surface radiative facing. This is a diagnostic hypothesis.
 angle=np.deg2rad(c.get('direction',c.get('wind_direction_deg',270)));wind=np.array([-np.sin(angle),-np.cos(angle),0]);delta=xyz[:,None,:]-xyz[None,:,:];along=np.einsum('ijk,k->ij',delta,wind);cross2=np.maximum((delta[:,:,:2]**2).sum(2)-along**2,0);z=delta[:,:,2];width=1.5+.35*np.maximum(along,0);center=.45*np.maximum(along,0);plume=np.exp(-cross2/(2*width**2)-(z-center)**2/(2*width**2))/(4*np.pi*(1+along**2+cross2+z**2));plume[along<0]*=.1;np.fill_diagonal(plume,0)
 return np.array(rad),plume

def features(c):
 g=c['g'];r,p=kernels(c['config'],g);state=c['state'];power=state[:,:,3]*np.array([n['area'] for n in g['nodes']])[None,:];radiative=np.einsum('hij,tj->tih',r,power)/100;plume=power@p.T/100;src=np.array([min(t/.1,1) if t<=20 else max(0,1-(t-20)/.1) for t in c['time']])[:,None]*g['source_kernel'][None,:]*12
 return np.concatenate([radiative,plume[:,:,None],src[:,:,None],state[:,:,3:4]/1000,(state[:,:,0:1]-20)/500],axis=2)

selected=json.loads((ROOT/'data/component_frozen/model.json').read_text());train=selected['training_cases'];manifest=json.loads((ROOT/'component-development.json').read_text());validation=[c['case'] for c in manifest['cases'] if c['split']=='validation'];cases={}
for name in train+validation:
 raw=json.loads((ROOT/'data/component_states'/f'{name}.json').read_text());c=hot.series(raw);c['config']=raw['configuration'];c['features']=features(c);cases[name]=c
coef=[]
for q in [0,1]:
 indices=[0,1,2,4,5] if q==0 else [0,1,2,3,4,5,6];xs=[];ys=[];ws=[]
 for name in train:
  c=cases[name];mask=np.array([n['kind']=='building' for n in c['g']['nodes']]);x=c['features'][:,mask][:,:,indices];xs.extend(x.reshape(-1,len(indices)));ys.extend(c['heat'][:,mask,q].ravel());ws.extend(np.full(x.shape[0]*x.shape[1],1/(x.shape[0]*x.shape[1])))
 x=np.array(xs);y=np.array(ys);w=np.sqrt(ws);lo=np.zeros(len(indices));hi=np.full(len(indices),np.inf)
 if q==1:lo[-1]=-np.inf;hi[-1]=0
 fit=lsq_linear(x*w[:,None],y*w,bounds=(lo,hi),tol=1e-10);assert fit.success;coef.append((indices,fit.x))
rows=[]
for name in validation:
 c=cases[name];b=np.array([n['kind']=='building' for n in c['g']['nodes']]);f=c['features'][:,b];h=np.stack([f[:,:,ind]@co for ind,co in coef],axis=2);truth=c['heat'][:,b];dose=np.trapezoid(np.maximum(h[:,:,0],0)+np.maximum(h[:,:,1],0),c['time'],axis=0);ref=np.trapezoid(np.maximum(truth[:,:,0],0)+np.maximum(truth[:,:,1],0),c['time'],axis=0);exp=ref>=100;roof=np.array([n['normal']==[0,0,1] for n in c['g']['nodes']])[b]
 g=apply(c['g'],c['config']);old=np.array([exchange.predict(selected,g,state,t) for state,t in zip(c['state'],c['time'])])[:,b];old_dose=np.trapezoid(np.maximum(old[:,:,0],0)+np.maximum(old[:,:,1],0),c['time'],axis=0)
 rows.append(dict(original_true_state_roof_mean_dose=float(old_dose[roof].mean()) if roof.any() else None,case=name,median_exposed_dose_error=float(np.median(abs(dose[exp]-ref[exp])/ref[exp])) if exp.any() else None,roof_reference_mean_dose=float(ref[roof].mean()) if roof.any() else None,roof_predicted_mean_dose=float(dose[roof].mean()) if roof.any() else None))
out=dict(training_cases=train,validation=rows,coefficients=[dict(indices=i,values=v.tolist()) for i,v in coef],scope='Measured FDS component states supplied during both fit and validation. Transport-only diagnostic, NOT autonomous model performance. Frozen Stage C code/predictions unchanged. Three canopy emitter heights and separate plume convection are hypotheses; no physical calibration claimed.')
(ROOT/'results/vertical-heat-transport-diagnostic.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
