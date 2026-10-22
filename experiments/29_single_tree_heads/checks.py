import json,hashlib
import numpy as np
import torch
from original_cnn import ROOT,cond,decode
from models import make
p=ROOT.parent/'28_single_tree_repair';f=json.loads((p/'results/prediction-freeze.json').read_text());assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in f['files'].items())
cs=json.loads((ROOT/'cases.json').read_text());assert len(cs)==38 and all(c['split'] in ['train','validation'] for c in cs)
m=make('heads');x=torch.from_numpy(cond(cs[0],np.array([0.,20.,60.,180.])))
with torch.no_grad():z=m(x);a=decode(z.numpy(),cs[0]['wind_speed']);q=torch.expm1(m.strength(x)).numpy()
integral=a[:,1].sum((1,2,3))*.125;err=np.max(abs(integral-q)/np.maximum(q,1e-8));assert err<1e-4;assert a[:,0].min()>=float(m.floor_C)-1e-5;assert np.isfinite(a).all()
r=dict(parent_freeze_verified=True,only_development_cases=True,temperature_floor_C=float(m.floor_C),spatial_integral_matches_predicted_strength_max_relative_error=float(err),note='Structural checks on the initialized separate-head model; no evidence of accuracy or physical conservation.');(ROOT/'results/structural-checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
