"""One local controller: wait for the existing submission, collect, analyze and archive."""
from pathlib import Path
import fcntl,json,subprocess,time
R=Path(__file__).resolve().parent;repo=R.parents[2]
def main():
 with (R/'data/finish-run.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);deadline=time.monotonic()+1800
  while not (R/'results/execution.json').exists():
   if time.monotonic()>deadline:raise TimeoutError('Existing submission did not create an execution record. Investigate; never resubmit automatically.')
   time.sleep(15)
  time.sleep(15)
  subprocess.run([str(repo/'.venv/bin/dvc'),'repro','--single-item',str(R/'dvc.yaml')+':cloud_collect'],cwd=repo,check=True)
  subprocess.run([str(repo/'.venv/bin/python'),str(R/'finalize_archive.py')],cwd=repo,check=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  (R/'results/finish-run-error.json').write_text(json.dumps(dict(error=repr(e),time_unix=time.time()),indent=2));raise
