"""Local analysis and archival only; never launches or retries cloud compute."""
from pathlib import Path
import fcntl,hashlib,json,subprocess,time,sys,math
R=Path(__file__).resolve().parent;repo=R.parents[2];py=repo/'.venv/bin/python';dvc=repo/'.venv/bin/dvc';hf=repo/'.venv/bin/hf'
def run(args):subprocess.run([str(x) for x in args],cwd=repo,check=True)
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 with (R/'data/archive-finalizer.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);deadline=time.monotonic()+5*3600
  while not (R/'results/collected.json').exists():
   if (R/'results/collection-error.json').exists():raise RuntimeError('Collector reports incomplete/failed run. Preserve partials and diagnose; no compute retry.')
   if time.monotonic()>deadline:raise TimeoutError('Collector did not complete in five hours')
   time.sleep(30)
  time.sleep(15)
  assert read(R/'results/permission-removed.json')['removed'] and not any(read(R/'results/cleanup.json').values())
  dest=R/'data/collected';report=read(dest/'report.json');done=read(dest/'complete.json');assert done['success'] and sha(dest/'report.json')==done['report_sha256'];expected=[];cuda=[]
  for arm in report['arms']:
   name=arm['arm'];epochs=arm['epochs'];steps=epochs*math.ceil((91 if name=='single' else 728)/4);cuda.append(read(dest/(name+'-cuda-check.json')))
   for ep in range(epochs+1):expected.extend(name+f'-epoch-{ep:03}'+s for s in ['.pt','.json','-statistics.npz'])
   expected.extend(name+f'-step-{step:06}.pt' for step in range(250,steps+1,250));expected.extend([name+'-report.json',name+'-selected.pt'])
  assert all(v['passed'] for v in cuda) and len({v['initial_model_sha256'] for v in cuda})==1
  missing=[n for n in expected if not (dest/n).is_file()];assert not missing,missing
  proof=dict(complete=True,expected_files=len(expected),checkpoint_count=sum(n.endswith('.pt') for n in expected),files={n:dict(bytes=(dest/n).stat().st_size,sha256=sha(dest/n)) for n in expected},cleanup_verified=True,exact_input_grant_removed=True,scope='Every expected epoch and250-update checkpoint/report/statistics present, SHA256 inventory; report hash matches worker completion. Remote archive verifies paths/sizes plus sampled hashes separately.')
  (R/'data/checkpoint-inventory.json').write_text(json.dumps(proof,indent=2)+'\n');(R/'results/archive-preservation.json').write_text(json.dumps({k:v for k,v in proof.items() if k!='files'},indent=2)+'\n')
  if '--inventory-only' in sys.argv:return
  run([py,R/'analyze.py']);run([dvc,'commit','-f',str(R/'dvc.yaml')+':analysis']);run([dvc,'commit','-f',str(R/'dvc.yaml')+':archive_inventory'])
  run([dvc,'push','-r','mirror',*[str(R/'dvc.yaml')+':'+s for s in ['decode_inputs','package','cloud_collect','analysis','archive_inventory']]])
  run([hf,'buckets','sync',repo/'FDS/hf_dvc_mirror','hf://buckets/wdavies/dvc_storage/wildfire3d','--no-delete','--ignore-existing']);run([py,repo/'scripts/verify_public_model_archive.py'])
  verified=read(repo/'experiments/33_representation_loss/results/public-archive-verification.json');assert verified['verified'];budget=read(repo/'experiments/33_representation_loss/budget.json')
  (R/'results/archive-complete.json').write_text(json.dumps(dict(complete=True,public_archive=verified,reservations_usd=budget['reserved_usd'],cap_usd=budget['authorized_usd'],invoice='unknown',completed_unix=time.time()),indent=2)+'\n')
  run(['git','add',R,repo/'experiments/33_representation_loss/budget.json',repo/'experiments/33_representation_loss/results/public-archive-verification.json',repo/'experiments/33_representation_loss/results/archive-status.json']);run(['git','commit','-m','Preserve continuous U-Net fitting results, curves and checkpoint archive']);run(['git','push','origin','codex/ignition-surrogate-pilot'])
if __name__=='__main__':
 try:main()
 except Exception as e:
  (R/'results/archive-finalizer-error.json').write_text(json.dumps(dict(error=repr(e),time_unix=time.time()),indent=2));raise
