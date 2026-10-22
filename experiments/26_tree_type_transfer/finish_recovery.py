"""One-shot recovery collection then original fit/freeze/test evaluation; no retries."""
import fcntl,time,json,subprocess,sys,traceback
from cloud import ROOT,read,save,collect
from extract import extract
lock=(ROOT/'data/recovery.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
 deadline=time.time()+6000
 while time.time()<deadline:
  r=collect('t26-recovery-0')
  if r['state']=='ACTIVE':time.sleep(45);continue
  assert not r.get('collection_error') and r.get('all_full_horizon'),r
  break
 else:raise RuntimeError('Recovery collection deadline; no retry')
 for c in read('cases.json'):
  if c['split'] not in ['train','validation']:continue
  raw=read('data/cloud/'+c['case']+'/result.json');assert raw['full_horizon']
  if not (ROOT/'data/extracted'/(c['case']+'.json')).exists():extract(c)
 save('results/development-summary.json',dict(full_horizon=True,configurations=26,recovered_group='t26-recovery-0',test_outputs_read=False))
 p=subprocess.run([sys.executable,'finish_pipeline.py'],cwd=ROOT);assert p.returncode==0
except Exception:
 (ROOT/'results/recovery-error.txt').write_text(traceback.format_exc());raise
