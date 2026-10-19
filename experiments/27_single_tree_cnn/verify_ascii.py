"""Cross-check raw 3D HRR values with NIST fds2ascii export at the36s pilot frame."""
import json,subprocess
import numpy as np
from fields import ROOT,read_slice
out=ROOT/'data/ascii-check';out.mkdir(exist_ok=True);rows=[]
for name in ['s27_pilot_0','s27_pilot_1','s27_pilot_2','s27_pilot_3']:
 folder=ROOT/'data/cloud'/name;target=out/(name+'.csv')
 answer=f'{name}\n2\n1\nn\n35 37\n1\n2\n{target}\n'
 p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=answer,text=True,capture_output=True,timeout=120,check=True);target.with_suffix('.log').write_text(p.stdout+p.stderr)
 q=np.loadtxt(target,delimiter=',',skiprows=2);_,units,b,t,a=read_slice(next(folder.glob('*_1_2.sf')));mask=(t>=35)&(t<=37);assert mask.sum()==1
 expected=a[mask][0].ravel(order='F');assert q.shape[0]==len(expected)
 error=float(abs(q[:,-1]-expected).max());scale=max(float(expected.max()),1);assert error/scale<1e-4
 rows.append(dict(case=name,quantity='HRRPUV',units=units,window_s=[35,37],max_relative_to_peak_export_error=error/scale,raw_csv=str(target.relative_to(ROOT))))
(ROOT/'results/ascii-verification.json').write_text(json.dumps(rows,indent=2));print(rows)
