"""Freeze all forecast arrays before new test FDS execution."""
import json,time,hashlib,math
import numpy as np
import torch
from original_cnn import CNN,prediction,load,ROOT
assert json.loads((ROOT/'results/physical-screen.json').read_text())['pass_all']
assert json.loads((ROOT/'results/full-validation.json').read_text())['pass_all']
cs=json.loads((ROOT/'cases.json').read_text());tests=[c for c in cs if c['split']=='test'];train=[c for c in cs if c['split']=='train'];t=np.arange(0,181,2,dtype=float)
assert not (ROOT/'results/prediction-freeze.json').exists(),'Never overwrite a freeze'
for name in ['original','physical']:
 m=CNN().to('mps' if torch.backends.mps.is_available() else 'cpu');m.load_state_dict(torch.load(ROOT/f'data/models/{name}.pt',map_location=next(m.parameters()).device,weights_only=True));m.eval()
 for c in tests:np.save(ROOT/f"data/predictions/{name}_{c['case']}.npy",prediction(m,c,t))
for c in tests:
 feat=lambda q:np.array([q['wind_speed']/4,math.cos(math.radians(q['angle_deg'])),math.sin(math.radians(q['angle_deg']))])
 ds=np.array([np.linalg.norm(feat(c)-feat(q)) for q in train]);ix=np.argsort(ds)[:3];ws=1/np.maximum(ds[ix],.01)**2;ws/=ws.sum();base=None
 for j,w in zip(ix,ws):
  a,ts=load(train[j]);ids=abs(ts[:,None]-t).argmin(0);term=np.array(a[ids]);term[:,2]-=train[j]['wind_speed'];term*=w;base=term if base is None else base+term
 base[:,2]+=c['wind_speed'];np.save(ROOT/f"data/predictions/interpolation_{c['case']}.npy",base)
files=[* (ROOT/'data/predictions').glob('*.npy'),ROOT/'data/models/original.pt',ROOT/'data/models/physical.pt',ROOT/'original_cnn.py',ROOT/'repair.py',ROOT/'cases.json',ROOT/'results/input-freeze.json',ROOT/'freeze.py']
(ROOT/'results/prediction-freeze.json').write_text(json.dumps(dict(created_unix=time.time(),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},selection='Existing validation only; all fresh test fields unavailable; original and training interpolation frozen with repaired CNN.'),indent=2));print('FROZEN',flush=True)
