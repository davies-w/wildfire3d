"""Single collection/local-archive owner; never launches compute or public uploads."""
from pathlib import Path
import fcntl,subprocess,json,hashlib,time
R=Path(__file__).resolve().parent;repo=R.parents[2];dvc=repo/'.venv/bin/dvc'
def run(*args):subprocess.run([str(x) for x in args],cwd=repo,check=True)
with (R/'data/finish.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  run(dvc,'repro','--single-item',str(R/'dvc.yaml')+':cloud_collect')
  assert json.loads((R/'results/collected.json').read_text())['complete']
  manifest=json.loads((R/'data/collected/manifest.json').read_text())
  for n,h in manifest.items():assert hashlib.sha256((R/'data/collected'/n).read_bytes()).hexdigest()==h,n
  assert sum(n.endswith('-selected.pt') for n in manifest)==8
  run(dvc,'repro','--single-item',str(R/'dvc.yaml')+':analysis')
  run(dvc,'push','-r','mirror',str(R/'dvc.yaml')+':cloud_collect',str(R/'dvc.yaml')+':analysis')
  (R/'results/local-archive-complete.json').write_text(json.dumps(dict(complete=True,manifest_files=len(manifest),selected_models=8,sha256_verified=True,public_upload=False,time_unix=time.time()),indent=2))
  run('git','add',R,repo/'experiments/33_representation_loss/budget.json')
  run('git','commit','-m','Preserve eight-size learning curve and local archive proof');run('git','push')
 except Exception as e:
  (R/'results/controller-error.json').write_text(json.dumps(dict(error=repr(e))));raise
