"""Validate six full coverage solves and their unchanged vegetation sampling before dispatch."""
from pathlib import Path
import json,subprocess,tarfile,hashlib
import numpy as np
from cloud import G,read,save,active_groups
from material_reader import frames
R=Path(__file__).parent
def main():
 g=next(g for g in active_groups() if g['phase']=='coverage');assert read('jobs/'+g['id']+'/completion.json')['all_full_horizon'];cases={c['case']:c for c in read('cases.json')};geoms=dict(np.load(R/'data/coverage-geometries.npz'));audit=[]
 for n in g['cases']:
  c=cases[n];m=json.loads((R/'data/summaries'/(n+'.json')).read_text());p=R/'data/downloads'/(n+'.tar.gz');p.parent.mkdir(exist_ok=True)
  if not p.exists():subprocess.run([G,'storage','cp','gs://tmrw-wildfire-20261015-trial/density36/'+g['id']+'/'+n+'.tar.gz',str(p)],check=True)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==m['raw_sha256'];dest=R/'data/coverage';dest.mkdir(exist_ok=True)
  if not (dest/n/'result.json').exists():
   with tarfile.open(p) as tar:tar.extractall(dest,filter='data')
  folder=dest/n;ps=next(ps for t,ps,l in frames(folder/(n+'_1.prt5')) if len(ps[0][0]));actual=np.zeros_like(geoms[n])
  for k,(x,q) in enumerate(ps[:4]):
   assert len(x)==400;ix=(x/.5).astype(int);np.add.at(actual[k],tuple(ix.T),q[:,1]*q[:,2]/.125)
  error=float(abs(actual-geoms[n]).max());assert error<1e-4,(n,error)
  assert m['result']['full_horizon'] and m['resume']['passed'];assert len(list(folder.glob('*.sf')))>=6
  for rr in m['checkpoint_manifest']['files']:assert hashlib.sha256((folder/rr['name']).read_bytes()).hexdigest()==rr['sha256']
  audit.append(dict(case=n,moisture=c['moisture'],seed=c['seed'],height=c['crown_height_m'],density_error=error,wall_seconds=m['result']['wall_seconds'],initial_wet_mass_kg=float(actual.sum()*.125),passed=True))
 save('results/coverage-review.json',dict(passed=True,cases=audit,scope='Full horizon, checkpoint hashes, exact frozen weighted initial density and moisture; not physical validation'))
 print('COVERAGE_PASSED',flush=True)
if __name__=='__main__':main()
