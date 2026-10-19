"""Full180s/91-frame field generation; exclude loading, compression and rendering."""
import json,time,resource,hashlib
import numpy as np,torch
from cnn import ROOT,CNN,prediction
f=json.loads((ROOT/'results/prediction-freeze.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['case']=='s27_test_0')
state=torch.load(ROOT/'data/models/cnn_32.pt',map_location='cpu',weights_only=True)
rows=[]
for device in ['cpu']+(['mps'] if torch.backends.mps.is_available() else []):
 m=CNN().to(device);m.load_state_dict(state);m.eval();runs=[]
 for i in range(4):
  if device=='mps':torch.mps.synchronize()
  r0=resource.getrusage(resource.RUSAGE_SELF);start=time.perf_counter();a=prediction(m,c,np.arange(0,181,2,dtype=float))
  if device=='mps':torch.mps.synchronize()
  dt=time.perf_counter()-start;r1=resource.getrusage(resource.RUSAGE_SELF)
  assert a.shape==(91,6,48,32,32) and np.isfinite(a).all()
  runs.append(dict(elapsed_s=dt,process_CPU_s=r1.ru_utime+r1.ru_stime-r0.ru_utime-r0.ru_stime))
 rows.append(dict(device=device,first_run=runs[0],warm_runs=runs[1:],warm_median_elapsed_s=float(np.median([r['elapsed_s'] for r in runs[1:]]))))
r=dict(frames=91,physical_horizon_s=180,shape=[91,6,48,32,32],rows=rows,scope='Standalone field generation, weights loaded once. Includes device transfer and decoding; excludes imports/model loading, disk writing and rendering. Local Apple hardware vs separate cloud FDS hardware; not a hardware-controlled speedup.')
(ROOT/'results/inference-benchmark.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
