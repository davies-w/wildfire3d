"""Local startup checks only; no cloud submissions."""
import csv,json,os,subprocess
from pathlib import Path
import numpy as np
from scene import ROOT
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
results=[]
for source in sorted((ROOT/'inputs/corrective_candidates').glob('*.fds')):
 name=source.stem;w=ROOT/'data/corrective_preflight'/name;w.mkdir(parents=True,exist_ok=True)
 s=source.read_text().replace('&TIME T_END=180 /','&TIME T_END=1.05 /').replace('&TIME T_END=90 /','&TIME T_END=1.05 /')
 assert 'T_END=1.05' in s
 (w/'check.fds').write_text(s)
 with (w/'run.log').open('w') as f:p=subprocess.run([str(binary),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=240)
 assert p.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower(),name
 with (w/(name+'_devc.csv')).open() as f:
  it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];a=np.array([list(map(float,row)) for row in it]);d=dict(zip(keys,a.T))
 assert np.isfinite(a).all()
 r=dict(case=name,passed=True,scope='Startup and device consistency only; not successful sustained ignition or domain independence.')
 if 'large_crown' in name:
  total=sum(v for k,v in d.items() if k.startswith('mass '));small=sum(v for k,v in d.items() if k.startswith('small mass '));large=sum(v for k,v in d.items() if k.startswith('large mass '));error=float(max(abs(total-small-large)));assert error<1e-4,error
  r.update(initial_small_wet_mass_kg=float(small[1]),initial_large_wet_mass_kg=float(large[1]),max_partition_mass_error_kg=error)
 results.append(r);print(r,flush=True)
(ROOT/'results/corrective-preflight.json').write_text(json.dumps(results,indent=2))
