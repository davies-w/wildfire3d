"""Finish archival only after the existing collector completes. Never submits compute."""
from pathlib import Path
import fcntl,hashlib,json,subprocess,time,sys
R=Path(__file__).resolve().parent;repo=R.parents[2];py=repo/'.venv/bin/python';dvc=repo/'.venv/bin/dvc';hf=repo/'.venv/bin/hf'
def run(args):subprocess.run([str(x) for x in args],cwd=repo,check=True)
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
def main():
 with (R/'data/archive-finalizer.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  deadline=time.monotonic()+4*3600
  while not (R/'results/collected.json').exists():
   if (R/'results/collection-error.json').exists():raise RuntimeError('Collector reported an error; no archive completion claim')
   if time.monotonic()>deadline:raise TimeoutError('Existing collector did not finish within four hours')
   time.sleep(30)
  time.sleep(15) # Let the collector finish its DVC lock update.
  assert read(R/'results/permission-removed.json')['removed']
  assert not any(read(R/'results/cleanup.json').values())
  dest=R/'data/collected';report=read(dest/'report.json');done=read(dest/'complete.json');assert done['success'] and sha(dest/'report.json')==done['report_sha256']
  expected=[];cuda=[]
  for m in report['models']:
   frame=m['frame'];epochs=m['epochs'];prefix=f'time-{frame:03}'
   cuda.append(read(dest/(prefix+'-cuda-check.json')))
   for ep in range(epochs+1):
    expected.extend([f'{prefix}-epoch-{ep:03}{suffix}' for suffix in ['.pt','.json','-counts.npz']])
   expected.extend(f'{prefix}-step-{step:06}.pt' for step in range(500,epochs*45+1,500))
  missing=[n for n in expected if not (dest/n).is_file()];assert not missing,missing
  assert all(c['passed'] for c in cuda) and len({c['initial_model_sha256'] for c in cuda})==1
  proof=dict(complete=True,expected_files=len(expected),checkpoint_count=sum(n.endswith('.pt') for n in expected),files={n:dict(bytes=(dest/n).stat().st_size,sha256=sha(dest/n)) for n in expected},cleanup_verified=True,exact_input_grant_removed=True,scope='Local presence and SHA256 inventory of every prescribed epoch/500-step checkpoint, epoch report and counts file. Completion report hash matches worker marker. No claim of separately provided remote per-checkpoint SHA256.')
  (R/'data/checkpoint-inventory.json').write_text(json.dumps(proof,indent=2));(R/'results/archive-preservation.json').write_text(json.dumps({k:v for k,v in proof.items() if k!='files'},indent=2))
  if '--inventory-only' in sys.argv:return
  run([py,R/'analyze.py'])
  run([dvc,'commit','-f',str(R/'dvc.yaml')+':analysis'])
  run([dvc,'commit','-f',str(R/'dvc.yaml')+':archive_inventory'])
  run([dvc,'push','-r','mirror',str(R/'dvc.yaml')+':cloud_collect',str(R/'dvc.yaml')+':analysis',str(R/'dvc.yaml')+':archive_inventory'])
  run([hf,'buckets','sync',repo/'FDS/hf_dvc_mirror','hf://buckets/wdavies/dvc_storage/wildfire3d','--no-delete','--ignore-existing'])
  run([py,repo/'scripts/verify_public_model_archive.py'])
  proof=read(repo/'experiments/33_representation_loss/results/public-archive-verification.json');assert proof['verified']
  (R/'results/archive-complete.json').write_text(json.dumps(dict(complete=True,public_archive=proof,reservations_usd=109.10,cap_usd=125,invoice='unknown',completed_unix=time.time()),indent=2))
  paths=[R/'dvc.yaml',R/'dvc.lock',R/'.gitignore',R/'analyze.py',R/'README.md',R/'finalize_archive.py',R/'results',repo/'experiments/33_representation_loss/budget.json',repo/'experiments/33_representation_loss/results/public-archive-verification.json',repo/'experiments/33_representation_loss/results/archive-status.json']
  run(['git','add',*paths]);run(['git','commit','-m','Preserve all ten HOT model checkpoints and verify public DVC archive']);run(['git','push','origin','codex/ignition-surrogate-pilot'])
if __name__=='__main__':
 try:main()
 except Exception as e:
  (R/'results/archive-finalizer-error.json').write_text(json.dumps(dict(error=repr(e),time_unix=time.time()),indent=2));raise
