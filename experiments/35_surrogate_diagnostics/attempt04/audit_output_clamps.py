"""Inference-only checkpoint audit; no optimizer or training, seven nominal times."""
from pathlib import Path
import json,hashlib
import numpy as np
import torch
from geometry_model import GeometryCNN,features
from original_cnn import cond,CNN
R=Path(__file__).parent
torch.set_num_threads(4)
c=next(c for c in json.loads((R/'cases.json').read_text()) if c['case']=='x32_033_s0')
t=np.array([0.,10.,20.,30.,60.,120.,180.]);g=np.load(R/'data/geometries.npz')[c['case']]
x=torch.from_numpy(np.concatenate([cond(c,t),np.repeat(features(g)[None],len(t),axis=0),np.full((len(t),1),(c['moisture']-.12)/.18,np.float32)],axis=1))
result={'case':c['case'],'times_s':t.tolist(),'scope':'Inference only on seven nominal times, not full-history truth comparison. Negative pre-clamp outputs have zero direct clamp derivative. Shared parameters can still change through other channels. This does not alone prove the sole cause of poor fitting.','checkpoints':{}}
for label,path in [('initial',R/'data/initial/single.pt'),('low',R/'data/collected/low-epoch-080.pt'),('restart',R/'data/collected/restart-epoch-080.pt')]:
 m=GeometryCNN();m.load_state_dict(torch.load(path,map_location='cpu',weights_only=False)['model']);m.eval();rows=[]
 with torch.no_grad():
  for i,time in enumerate(t):
   raw=CNN.forward(m,x[i:i+1]);rows.append({'time_s':float(time),'channels':{str(ch):{'raw_min':float(raw[:,ch].min()),'raw_max':float(raw[:,ch].max()),'fraction_below_zero':float((raw[:,ch]<0).float().mean()),'fraction_above_ten':float((raw[:,ch]>10).float().mean())} for ch in [1,5]}})
 result['checkpoints'][label]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':rows}
(R/'results/output-clamp-audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
