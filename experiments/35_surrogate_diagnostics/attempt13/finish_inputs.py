"""Wait for full local extraction, validate and package. Never launches paid compute."""
from pathlib import Path
import fcntl,time,json,subprocess
R=Path(__file__).resolve().parent;repo=R.parents[2];P=R.parent/'attempt12'
def run(xs):subprocess.run([str(x) for x in xs],cwd=repo,check=True)
with (R/'data/input-finalizer.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);deadline=time.monotonic()+7200
 try:
  while not (P/'results/prepared.json').exists():
   if time.monotonic()>deadline:raise TimeoutError('Full dataset extraction incomplete')
   time.sleep(10)
  assert json.loads((P/'results/prepared.json').read_text())['histories']==520
  run([repo/'.venv/bin/dvc','commit','-f',str(P/'dvc.yaml')+':prepare'])
  run([repo/'.venv/bin/dvc','repro','--single-item',str(P/'dvc.yaml')+':validate'])
  run([repo/'.venv/bin/dvc','repro','--single-item',str(R/'dvc.yaml')+':prepare_data'])
  run([repo/'.venv/bin/dvc','repro','--single-item',str(R/'dvc.yaml')+':package'])
  (R/'results/inputs-ready.json').write_text(json.dumps(dict(passed=True,no_training_launched=True),indent=2))
 except Exception as e:
  (R/'results/input-finalizer-error.json').write_text(json.dumps(dict(error=repr(e))));raise
