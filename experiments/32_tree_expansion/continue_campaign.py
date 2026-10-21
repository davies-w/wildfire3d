"""Single stage coordinator; no paid retries and no duplicate development dispatcher."""
from pathlib import Path
import fcntl,json,time,subprocess,sys,traceback
R=Path(__file__).parent

def read(n):return json.loads((R/n).read_text())
def run(script):subprocess.run([sys.executable,str(R/script)],check=True)
def wait_file(path,errors):
 while not (R/path).exists():
  for error in errors:
   if (R/error).exists():raise RuntimeError(read(error))
  time.sleep(60)

def main():
 with (R/'data/campaign.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  wait_file('results/development-complete.json',['results/dispatcher-error.json'])
  assert read('results/development-complete.json')['complete']
  if not (R/'results/gpu-execution.json').exists():run('launch_learning.py')
  while not (R/'results/learning-collected.json').exists():run('collect_learning.py');time.sleep(60)
  if not (R/'results/test-simulations-complete.json').exists():run('dispatch_tests.py')
  if not (R/'results/evaluation-execution.json').exists():run('prepare_evaluation.py');run('launch_evaluation.py')
  while not (R/'results/evaluation-collected.json').exists():run('collect_evaluation.py');time.sleep(60)
  run('visualize_results.py')
  (R/'results/campaign-ready-for-report.json').write_text(json.dumps(dict(complete=True,time_unix=time.time(),scope='Simulations, fitting, frozen evaluation, selected animations and cleanup complete; human-readable interpretation and final DVC adoption still required'),indent=2))
if __name__=='__main__':
 try:main()
 except BaseException:
  (R/'results/campaign-error.json').write_text(json.dumps(dict(error=traceback.format_exc(),time_unix=time.time()),indent=2));raise
