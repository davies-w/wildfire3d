"""Shared nonnegative, temperature-driven fuel-release law; geometry supplies fuel mass."""
import numpy as np
from scipy.optimize import nnls
DENSITY=1.683+.289+.263+.394
HOC=17425.
def wet_mass(g):
 return np.array([np.pi*n['radius']**2*n['height']/3*DENSITY*(1+g['moisture']) if n['kind']=='vegetation' else 0 for n in g['nodes']])
def features(state):
 return np.column_stack([np.maximum(state[:,1]-t,0)/500 for t in [100,300,500,700,1000]]+[np.maximum(state[:,0]-t,0)/500 for t in [100,300]])
def fit(model,cases):
 xs=[];ys=[];ws=[]
 for c in cases:
  mask=np.array([n['kind']=='vegetation' for n in c['g']['nodes']]);mass=wet_mass(c['g']);st=c['state'];num=mask.sum()
  for k in range(len(st)-1):
   available=mass*np.maximum(st[k,:,2],0);keep=mask&(available>1)
   xs.extend(features(st[k])[keep]);ys.extend(st[k+1,keep,3]/available[keep]);ws.extend([1/(num*(len(st)-1))]*keep.sum())
 w=np.sqrt(ws);coef,_=nnls(np.array(xs)*w[:,None],np.array(ys)*w);model['release_coefficients']=coef.tolist();return model

def predict(model,g,state):
 available=wet_mass(g)*np.clip(state[:,2],0,1)
 rate=features(state)@np.array(model['release_coefficients'])
 return np.minimum(np.maximum(rate,0)*available,available*HOC/.5)
