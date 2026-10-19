"""One locked collector for already-submitted domain controls; no launches."""
import time,fcntl,traceback,subprocess,sys
from cloud import ROOT,collect,save
lock=(ROOT/'data/domain-collector.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
 deadline=time.time()+6600
 while time.time()<deadline:
  r=collect('s27-domain-0')
  if r['state']=='ACTIVE':time.sleep(40);continue
  assert not r.get('collection_error') and r['all_full_horizon'],r
  with (ROOT/'results/domain-check.log').open('w') as f:p=subprocess.run([sys.executable,str(ROOT/'domain_check.py')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=300)
  assert p.returncode==0
  break
 else:raise RuntimeError('Collector deadline exceeded; inspect cloud cleanup')
except Exception:
 (ROOT/'results/domain-error.txt').write_text(traceback.format_exc());raise
