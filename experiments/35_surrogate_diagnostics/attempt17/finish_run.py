"""Single local collector/archive owner. Never submits or retries cloud compute."""
from pathlib import Path
import fcntl,subprocess,json
R=Path(__file__).resolve().parent;repo=R.parents[2]
with (R/'data/finish.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  subprocess.run([str(repo/'.venv/bin/dvc'),'repro','--single-item',str(R/'dvc.yaml')+':cloud_collect'],cwd=repo,check=True)
  subprocess.run([str(repo/'.venv/bin/python'),str(R/'finalize_archive.py')],cwd=repo,check=True)
 except Exception as e:
  (R/'results/controller-error.json').write_text(json.dumps(dict(error=repr(e))));raise
