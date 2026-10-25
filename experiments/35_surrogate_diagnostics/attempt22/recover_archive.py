"""Archive-only recovery after HTTP429; sequential bounded upload batches, no compute."""
from pathlib import Path
import fcntl,subprocess,time
from huggingface_hub import HfApi
R=Path(__file__).resolve().parent;repo=R.parents[2]
with (R/'data/recovery.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 api=HfApi();source=repo/'FDS/hf_dvc_mirror';plan=api.sync_bucket(str(source),'hf://buckets/wdavies/dvc_storage/wildfire3d',ignore_existing=True,delete=False,dry_run=True,quiet=True)
 assert not any(o.action=='delete' for o in plan.operations)
 pending=[o for o in plan.operations if o.action=='upload'];print('Missing objects',len(pending),flush=True)
 for start in range(0,len(pending),25):
  batch=pending[start:start+25]
  api.batch_bucket_files('wdavies/dvc_storage',add=[(str(source/o.path),'wildfire3d/'+o.path) for o in batch])
  print('Archived',min(start+25,len(pending)),'of',len(pending),flush=True);time.sleep(2)
 subprocess.run([str(repo/'.venv/bin/python'),str(R/'finalize_archive.py')],cwd=repo,check=True)
