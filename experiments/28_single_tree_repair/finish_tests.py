"""Single locked collector; never submits or retries paid jobs."""
import fcntl,json,time,subprocess,sys
from pathlib import Path
from cloud import collect,ROOT
from fields import extract
with (ROOT/'data/collector.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 groups=json.loads((ROOT/'groups.json').read_text());deadline=time.monotonic()+3000
 pending={g['id'] for g in groups}
 while pending:
  if time.monotonic()>deadline:raise RuntimeError('Collector deadline exceeded; inspect cloud cleanup, no automatic retry')
  for name in sorted(pending.copy()):
   r=collect(name)
   if r.get('all_full_horizon'):
    for c in json.loads((ROOT/'cases.json').read_text()):
     if c['case'] in next(g for g in groups if g['id']==name)['cases']:extract(c)
    pending.remove(name);print('COLLECTED',name,flush=True)
   elif r['state']!='ACTIVE':raise RuntimeError(r)
  if pending:time.sleep(30)
 for script in ['evaluate_repair.py','animate_repair.py']:subprocess.run([sys.executable,str(ROOT/script)],check=True)
 (ROOT/'results/completion.json').write_text(json.dumps(dict(all_six_collected=True,cleanup_verified=True,finished_unix=time.time()),indent=2))
 print('COMPLETE',flush=True)
