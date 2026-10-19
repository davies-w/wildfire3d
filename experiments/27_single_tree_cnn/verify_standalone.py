"""Export and verify CPU inference using only code/weights, with no solver data."""
import hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).parent
f=json.loads((R/'results/prediction-freeze.json').read_text())
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
out=R/'data/standalone';out.mkdir(exist_ok=True)
shutil.copy2(R/'deployment-readme.txt',out/'README.txt')
for src in ['cnn.py','predict.py','data/models/cnn_32.pt']:
 shutil.copy2(R/src,out/Path(src).name)
c=next(c for c in json.loads((R/'cases.json').read_text()) if c['case']=='s27_test_0')
start=time.monotonic()
subprocess.run([sys.executable,'predict.py','--model','cnn_32.pt','--wind',str(c['wind_speed']),'--angle',str(c['angle_deg']),'--times','0,20,40,60,90,120,180','--out','prediction.npz'],cwd=out,check=True)
elapsed=time.monotonic()-start
v=np.load(out/'prediction.npz')['fields'];a=np.load(R/'data/predictions/cnn_32_s27_test_0.npy',mmap_mode='r')[[0,10,20,30,45,60,90]]
assert v.shape==a.shape and np.isfinite(v).all()
err=float(abs(v-a).max());assert np.allclose(v,a,atol=.03,rtol=1e-3),(err,'CPU/GPU disagreement')
r=dict(passed=True,device='CPU',frames=7,elapsed_seconds_including_process_start_compression=elapsed,maximum_absolute_difference_from_frozen_GPU_prediction=err,export_files=['cnn.py','predict.py','cnn_32.pt'],solver_data_present=False,scope='Numerical deployment check, not accuracy evidence. CPU only. No FDS invocation or reference-field inputs.')
(R/'results/standalone-check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
