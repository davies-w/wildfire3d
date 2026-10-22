"""Bounded authorized continuation: development -> fit -> freeze -> tests -> report.
No extra cases, retries, IAM changes or budget recycling. Every test launch
uses cloud.launch's freeze and reservation gates. Any failure stops this driver.
"""
import fcntl,json,time,subprocess,sys,traceback,hashlib
from cloud import ROOT,read,save,launch,collect
lock=(ROOT/'data/pipeline.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
deadline=time.time()+4*3600

def run(script,*args):
 with (ROOT/'results'/(script.replace('.py','')+'.log')).open('a') as log:
  p=subprocess.run([sys.executable,str(ROOT/script),*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=max(1,deadline-time.time()))
 assert p.returncode==0,script+' failed; inspect its log'

def wait_for(path):
 while not (ROOT/path).exists():
  assert time.time()<deadline,'Pipeline deadline reached; inspect cloud cleanup, no continuation'
  for p in ['results/development-collector-error.json','results/development-collector-error.txt','results/calibration-collector-error.json','results/calibration-collector-error.txt']:
   assert not (ROOT/p).exists(),'Collection failure: '+p
  time.sleep(30)

try:
 save('results/pipeline-status.json',dict(stage='waiting_for_development',new_paid_cases_allowed='Only the combined predeclared held-out group after prediction freeze',deadline_unix=deadline))
 wait_for('results/development-summary.json');wait_for('results/calibration-summary.json')
 assert read('results/development-summary.json')['full_horizon']
 run('validate_inputs.py')
 save('results/pipeline-status.json',dict(stage='fitting',deadline_unix=deadline))
 run('train.py','--epochs','150')
 # Selection used only the declared validation data, not any held-out output.
 report=read('data/models/training-report.json')
 assert report['parameters']<2000
 run('freeze_predictions.py')
 save('results/pipeline-status.json',dict(stage='frozen_test_predictions',deadline_unix=deadline))
 for name in ['t26-test-combined']:
  assert name not in read('budget.json')['reservations'],'Never repeat a reserved attempt'
  launch(name,2.2)
 save('results/pipeline-status.json',dict(stage='running_held_out_tests',deadline_unix=deadline))
 pending=['t26-test-combined']
 while pending:
  assert time.time()<deadline,'Test collection deadline reached; no retries'
  for name in list(pending):
   r=collect(name)
   if r['state']=='ACTIVE':continue
   assert not r.get('collection_error') and r.get('all_full_horizon'),r
   pending.remove(name)
  if pending:time.sleep(40)
 run('evaluate.py')
 save('results/pipeline-status.json',dict(stage='complete',summary='results/test-summary.json',reserved_usd=read('budget.json')['reserved_usd'],full_gas_field_validation=False))
 print('PIPELINE COMPLETE',flush=True)
except Exception:
 (ROOT/'results/pipeline-error.txt').write_text(traceback.format_exc());raise
