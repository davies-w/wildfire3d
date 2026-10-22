import json,subprocess,os,csv,hashlib
from pathlib import Path
import numpy as np
from scipy.io import FortranFile,FortranEOFError
ROOT=Path(__file__).parent;BINARY=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
def particles(folder,name):
 f=FortranFile(folder/(name+'_1.prt5'));f.read_ints();f.read_ints();nc=int(f.read_ints()[0]);nqs=[]
 for i in range(nc):
  n=int(f.read_ints()[0]);nqs.append(n)
  for _ in range(n):f.read_record('u1');f.read_record('u1')
 while True:
  t=float(f.read_reals('f4')[0]);parts=[]
  for n in nqs:
   count=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,count);f.read_ints();q=f.read_reals('f4').reshape(n,count) if n else []
   parts.append((xyz,q))
  if parts[0][0].shape[1]:return parts
rows=[];reference={}
for c in json.loads((ROOT/'cases.json').read_text()):
 name=c['case'];folder=ROOT/'data/preflight'/name;folder.mkdir(exist_ok=True)
 source=(ROOT/'decks'/f'{name}.fds').read_text().replace('T_END=180','T_END=.1').replace('DT_RESTART=30.','DT_RESTART=.05').replace('DT_DEVC=1.','DT_DEVC=.01').replace('DT_PART=2.','DT_PART=.05')
 env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0')
 def run(s,tag):
  (folder/'check.fds').write_text(s)
  with (folder/(tag+'.log')).open('w') as f:p=subprocess.run([str(BINARY),'check.fds'],cwd=folder,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  assert p.returncode==0 and 'completed successfully' in (folder/(tag+'.log')).read_text().lower(),(name,(folder/(tag+'.log')).read_text()[-3000:])
 run(source,'initial');assert list(folder.glob('*.restart'))
 pts=particles(folder,name)
 if c['layout'] not in reference:reference[c['layout']]=pts
 errors=[float(np.max(abs(p[0]-q[0]))) for p,q in zip(pts,reference[c['layout']])]
 mass=[float((p[1][1]*p[1][2]).sum()) for p in pts[:4]]
 assert max(errors)<1e-5,('particle coordinates differ across grids',errors)
 run(source.replace('T_END=.1','T_END=.15').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,'),'resume')
 rows.append(dict(case=name,passed=True,position_max_difference_m=max(errors),wet_mass_by_class_kg=mass))
 (ROOT/'results/preflight.json').write_text(json.dumps(rows,indent=2));print('PASS',name,mass,flush=True)
