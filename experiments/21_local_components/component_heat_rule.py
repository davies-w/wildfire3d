"""Low-capacity heat exchange heads: source strength/geometry, not target-temperature leakage into radiation."""
import numpy as np
from scipy.optimize import lsq_linear

def features(g,state,t):
 e=np.maximum(state[:,3],0);power=e*np.array([n['area'] for n in g['nodes']]);rad=g['kernel']@power
 if '_wind_kernel' not in g:g['_wind_kernel']=g['kernel']*g['aligned']
 wind=(g['_wind_kernel']@power)*g['wind_speed']/4
 pulse=max(0,min(t/.1,1)) if t<=20 else max(0,1-(t-20)/.1)
 return np.column_stack([rad/100,wind/100,g['source_kernel']*12*pulse,e/1000,(state[:,0]-20)/500])
def fit(model,cases):
 heads={}
 for kind in ['vegetation','building']:
  xs=[];ys=[];ws=[]
  for c in cases:
   mask=np.array([n['kind']==kind for n in c['g']['nodes']]);count=mask.sum()
   if not count:continue
   for k,t in enumerate(c['time']):xs.extend(features(c['g'],c['state'][k],t)[mask]);ys.extend(c['heat'][k,mask]);ws.extend([1/(count*len(c['time']))]*count)
  x=np.array(xs);y=np.array(ys);w=np.sqrt(np.array(ws));coef=[]
  for q in [0,1]:
   a=x[:,:4] if q==0 else x
   lo=np.zeros(a.shape[1]);hi=np.full(a.shape[1],np.inf)
   if q==1:lo[-1]=-np.inf;hi[-1]=0
   result=lsq_linear(a*w[:,None],y[:,q]*w,bounds=(lo,hi),tol=1e-10);assert result.success
   coef.append(result.x.tolist())
  heads[kind]=coef
 model['exchange_heads']=heads;return model

def predict(model,g,state,t):
 x=features(g,state,t);h=np.zeros((len(state),2));types=np.array([n['kind'] for n in g['nodes']])
 for kind,coef in model['exchange_heads'].items():
  mask=types==kind;h[mask,0]=x[mask,:4]@coef[0];h[mask,1]=x[mask]@coef[1]
 return h
