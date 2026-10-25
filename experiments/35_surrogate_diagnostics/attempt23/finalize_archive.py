"""Verify, analyze, preserve and publish completed results; never launches compute."""
from pathlib import Path
import json,hashlib,subprocess,fcntl,time
R=Path(__file__).resolve().parent;repo=R.parents[2];py=repo/'.venv/bin/python';dvc=repo/'.venv/bin/dvc'
def run(xs):subprocess.run([str(x) for x in xs],cwd=repo,check=True)
def main():
 with (R/'data/archive.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert json.loads((R/'results/collected.json').read_text())['complete']
  assert not any(json.loads((R/'results/cleanup.json').read_text()).values())
  assert json.loads((R/'results/permission-removed.json').read_text())['removed']
  D=R/'data/collected';manifest=json.loads((D/'manifest.json').read_text())
  for n,h in manifest.items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h,n
  assert len([n for n in manifest if n.endswith('-selected.pt')])==20
  run([dvc,'commit','-f',str(R/'dvc.yaml')+':cloud_collect']);run([dvc,'repro','--single-item',str(R/'dvc.yaml')+':analysis'])
  run([dvc,'push','-r','mirror',str(R/'dvc.yaml')]);run([py,R/'archive_upload.py']);run([py,repo/'scripts/verify_public_model_archive.py'])
  proof=json.loads((repo/'experiments/33_representation_loss/results/public-archive-verification.json').read_text());(R/'results/archive-complete.json').write_text(json.dumps(dict(complete=True,verified_files=len(manifest),public_archive=proof,invoice='unknown',completed_unix=time.time()),indent=2))
  run(['git','add',R,repo/'experiments/33_representation_loss/budget.json',repo/'experiments/33_representation_loss/results/public-archive-verification.json',repo/'experiments/33_representation_loss/results/archive-status.json']);run(['git','commit','-m','Preserve matched four-state gated-GRU comparison']);run(['git','push'])
if __name__=='__main__':
 try:main()
 except Exception as e:
  (R/'results/archive-error.json').write_text(json.dumps(dict(error=repr(e))));raise
