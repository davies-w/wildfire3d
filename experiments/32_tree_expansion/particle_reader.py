from pathlib import Path
import json,subprocess,os,hashlib
import numpy as np
from scipy.io import FortranFile
from scipy.spatial import cKDTree
R=Path(__file__).parent;B=R.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
def first(path):
 f=FortranFile(path);f.read_ints();f.read_ints();labels=[]
 for _ in range(int(f.read_ints()[0])):
  l=[]
  for _ in range(int(f.read_ints()[0])):l.append(f.read_record('u1').tobytes().decode().strip());f.read_record('u1')
  labels.append(l)
 while True:
  t=f.read_reals('f4')[0];parts=[]
  for l in labels:
   n=int(f.read_ints()[0]);x=f.read_reals('f4').reshape(3,n).T;f.read_ints();q=f.read_reals('f4').reshape(len(l),n).T if l else None;parts.append((x,q))
  if len(parts[0][0]):return parts

def main():
 cs=json.loads((R/'cases.json').read_text());expected=json.loads((R/'data/expected-particles.json').read_text());report=[];fuels=['foliage','small roundwood','medium roundwood','large roundwood']
 for i in [0,7,10]:
  c=cs[i];assert c['split']=='train';folder=R/'data/preflight'/c['case'];folder.mkdir(parents=True,exist_ok=True);source=(R/'decks'/(c['case']+'.fds')).read_text();short=source.replace('T_END=180','T_END=.1').replace('DT_PART=2.','DT_PART=.05');(folder/'check.fds').write_text(short)
  env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0');p=subprocess.run([str(B), 'check.fds'],cwd=folder,env=env,capture_output=True,text=True,timeout=90);(folder/'run.log').write_text(p.stdout+p.stderr);assert p.returncode==0 and 'completed successfully' in (folder/(c['case']+'.out')).read_text().lower()
  ps=first(folder/(c['case']+'_1.prt5'));checks=[]
  for k,fuel in enumerate(fuels):
   ex=[p for p in expected[c['case']] if p['fuel']==fuel];x,q=ps[k];dist,ix=cKDTree(x).query(np.array([p['xyz'] for p in ex]));assert len(x)==400 and len(set(ix))==400 and dist.max()<1e-5;err=float(np.max(abs(q[ix,2]/np.array([p['weight'] for p in ex])-1)));assert err<2e-6;checks.append(dict(fuel=fuel,max_position_error=float(dist.max()),max_weight_relative_error=err,mass_kg=float((q[:,1]*q[:,2]).sum())))
  report.append(dict(case=c['case'],passed=True,checks=checks,binary_sha256=hashlib.sha256(B.read_bytes()).hexdigest()))
 (R/'results/preflight.json').write_text(json.dumps(report,indent=2));print('All three scaled-particle preflights passed')
if __name__=='__main__':main()
