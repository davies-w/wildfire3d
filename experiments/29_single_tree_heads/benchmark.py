import json,time
import numpy as np,torch
from original_cnn import ROOT,prediction
from models import make
c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['split']=='validation');rows=[]
for kind in ['bounded','heads']:
 for device in ['cpu']+(['mps'] if torch.backends.mps.is_available() else []):
  m=make(kind);m.load_state_dict(torch.load(ROOT/f'data/models/{kind}.pt',map_location='cpu',weights_only=True));m.to(device).eval();times=[]
  for i in range(4):
   start=time.perf_counter();a=prediction(m,c,np.arange(0,181,2,dtype=float));times.append(time.perf_counter()-start);assert np.isfinite(a).all()
  rows.append(dict(model=kind,device=device,median_seconds=float(np.median(times[1:])),all_runs_seconds=times))
(ROOT/'results/benchmark.json').write_text(json.dumps(dict(rows=rows,scope='91 complete3D frames, includes transfer and decoding, excludes model loading, writing, rendering. No FDS input at inference.'),indent=2));print(json.dumps(rows,indent=2))
