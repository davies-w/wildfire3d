"""Build six-view payload from frozen predictions and extracted FDS time series. No solves."""
import json,hashlib
from pathlib import Path
import numpy as np
import component_hot_state_model as hot
from scene import ROOT
freeze=json.loads((ROOT/'results/component-test-prediction-freeze.json').read_text())
for p,h in freeze['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
output=[]
for name,title in [('c21_santa_rosa_east_03','Santa Rosa'),('c21_glen_ellen_06','Glen Ellen')]:
 raw=json.loads((ROOT/'data/component_test_states'/f'{name}.json').read_text());ref=hot.series(raw);g=ref['g'];nodes=g['nodes'];groups={}
 for i,n in enumerate(nodes):
  if n['kind']=='building':
   key=(*np.floor(np.array(n['xyz'])/2).astype(int),*n['normal']);groups.setdefault(key,[]).append(i)
 groups=list(groups.values());patches=[]
 for ids in groups:
  w=np.array([nodes[i]['area'] for i in ids]);xyz=np.average([nodes[i]['xyz'] for i in ids],axis=0,weights=w)
  patches.append(dict(xyz=np.round(xyz,3).tolist(),normal=nodes[ids[0]]['normal'],area=round(float(w.sum()),3)))
 ts=ref['time'];ix=np.unique(np.r_[np.arange(0,len(ts),6),len(ts)-1]);models=[]
 for label in ['FDS','Additive','Graph']:
  if label=='FDS':pred=ref
  else:
   suffix='baseline' if label=='Additive' else 'graph'
   with np.load(ROOT/'data/component_frozen'/f'{name}-{suffix}.npz') as f:pred={k:f[k] for k in f.files}
  q=np.maximum(pred['heat'][:len(ts),:,0],0)+np.maximum(pred['heat'][:len(ts),:,1],0)
  dose=np.vstack([np.zeros(q.shape[1]),np.cumsum((q[1:]+q[:-1])*.25,axis=0)])
  def group(a):return np.round(np.array([np.average(a[ix][:,ids],axis=1,weights=[nodes[i]['area'] for i in ids]) for ids in groups]).T,3).tolist()
  models.append(dict(name=label,heat=group(q),dose=group(dose),fuel=np.round(pred['state'][ix,:3,3]/17425,5).tolist()))
 c=raw['configuration'];output.append(dict(name=title,time=ts[ix].tolist(),patches=patches,canopies=c['canopies'],footprint=c['footprint_local']['coordinates'][0],height=c['building_height_m'],wind=c['wind_speed_m_s'],moisture=c['moisture'],models=models))
p=ROOT/'data/heat-comparison.json';p.write_text(json.dumps(output,separators=(',',':')))
print('Payload bytes',p.stat().st_size,'patch groups',[len(s['patches']) for s in output])
(ROOT/'data/heat-comparison.html').write_text((ROOT/'heat-comparison.template.html').read_text().replace('PAYLOAD',p.read_text()))
