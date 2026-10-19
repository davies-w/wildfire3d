"""Independent NIST fds2ascii check of temperature/HRR for the displayed test cases."""
import json,subprocess,hashlib
import numpy as np
from fields import ROOT,read_slice
f=json.loads((ROOT/'results/prediction-freeze.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
out=ROOT/'data/test-ascii-check';out.mkdir(exist_ok=True);rows=[]
for name in ['s27_test_0','s27_test_1']:
 folder=ROOT/'data/cloud'/name
 for field,quantity in [(1,'TEMPERATURE'),(2,'HRRPUV')]:
  target=out/f'{name}-{field}.csv';answer=f'{name}\n2\n1\nn\n59 61\n1\n{field}\n{target}\n'
  p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=answer,text=True,capture_output=True,timeout=120,check=True);target.with_suffix('.log').write_text(p.stdout+p.stderr)
  q=np.loadtxt(target,delimiter=',',skiprows=2);label,units,b,t,a=read_slice(next(folder.glob(f'*_1_{field}.sf')));mask=(t>=59)&(t<=61);assert mask.sum()==1 and label==quantity
  expected=a[mask][0].ravel(order='F');assert q.shape[0]==len(expected)
  error=float(abs(q[:,-1]-expected).max());scale=max(float(abs(expected).max()),1);assert error/scale<1e-4
  rows.append(dict(case=name,quantity=quantity,units=units,window_s=[59,61],actual_frame_time=float(t[mask][0]),maximum_export_value=float(q[:,-1].max()),max_relative_to_peak_export_error=error/scale,raw_csv=str(target.relative_to(ROOT))))
(ROOT/'results/test-ascii-verification.json').write_text(json.dumps(rows,indent=2));print(rows)
