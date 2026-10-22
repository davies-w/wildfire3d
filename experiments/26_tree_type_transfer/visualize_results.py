"""Export every case's measured canopy series and untouched predictions for browsing."""
import json,csv
import numpy as np
from pathlib import Path
from build import ROOT,MODELS,CLASSES
from model_data import geometry
out=[]
def rounded(x):return np.round(x,4).tolist()
def cumulative(t,y):return np.r_[0,np.cumsum((y[:-1]+y[1:])*.5*np.diff(t))]
for c in json.loads((ROOT/'cases.json').read_text()):
 g=geometry(c);a=np.load(ROOT/'data/extracted'/(c['case']+'.npz'));t=a['time'];raw=a['state'].reshape(len(t),-1,6)[:,g['indices']];inst=g['instance'].numpy()
 with (ROOT/'data/cloud'/c['case']/(c['case']+'_devc.csv')).open() as f:rr=list(csv.reader(f))
 keys=[v.strip().strip('"') for v in rr[1]];dv=np.array([[float(v) for v in row] for row in rr[2:] if row]);dt=dv[:,0]
 item=dict(id=c['case'],split=c['split'],family=c['family'],trees=c['trees'],heater=c['heater_xy'],strength=c['strength'],duration=c['duration'],series=[])
 ground=np.array([dv[:,i] for i,k in enumerate(keys) if k.startswith('ground_') and k.endswith('_T')]);item['ground']={'t':rounded(t),'mean':rounded(np.interp(t,dt,ground.mean(0))),'max':rounded(np.interp(t,dt,ground.max(0)))}
 for i,tree in enumerate(c['trees']):
  mask=inst==i;r=raw[:,mask];rate=sum(dv[:,keys.index(f'v{i} fuel {f}')] for f in CLASSES)
  obs={'name':'FDS','t':rounded(t),'y':[rounded(r[:,:,0].mean(1)),rounded(r[:,:,1].sum(1)),rounded(r[:,:,2].mean(1)),rounded(r[:,:,3].mean(1)),rounded(np.interp(t,dt,rate)),rounded(np.interp(t,dt,cumulative(dt,rate)))]}
  series=[obs]
  if c['split'].endswith('test'):
   for label,name in [('single_composed','Singles only'),('pair_adapted','Pair trained'),('independent_additive','Additive')]:
    p=np.load(ROOT/'data/predictions'/f"{c['case']}__{label}.npz");pt=p['time'];m=p['instance']==i;rate=p['rate'][:,m].sum(1);heat=p['heat'][:,m].mean(1)
    series.append({'name':name,'t':rounded(pt),'y':[rounded((p['state'][:,m,0]*1000+20).mean(1)),rounded((p['state'][:,m,1]*g['static'][m,9].numpy()).sum(1)),rounded(np.r_[heat[:,0],heat[-1,0]]),rounded(np.r_[heat[:,1],heat[-1,1]]),rounded(np.r_[rate,rate[-1]]),rounded(np.r_[0,np.cumsum(rate*np.diff(pt))])]})
  item['series'].append(series)
 out.append(item)
data={'models':MODELS,'cases':out,'metrics':[['Regional mean temperature','°C'],['Remaining wet + solid mass','kg'],['Incident radiation','kW/m²'],['Convective heat flux','kW/m²'],['Fuel-vapor release rate','kg/s'],['Cumulative fuel-vapor release','kg']]}
(ROOT/'results/visuals/all-cases.json').write_text(json.dumps(data,separators=(',',':')))
print(len(out),'cases; bytes', (ROOT/'results/visuals/all-cases.json').stat().st_size)
