"""Single locked collector. Never submits or retries paid jobs."""
import fcntl,time,json,traceback
from cloud import ROOT,read,save,collect
from fields import extract
lock=(ROOT/'data/pilot-collector.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
pending=['s27-pilot-0','s27-pilot-1'];deadline=time.time()+6600
try:
 while pending:
  assert time.time()<deadline
  for name in pending[:]:
   r=collect(name)
   if r['state']=='ACTIVE':continue
   assert not r.get('collection_error') and r['all_full_horizon'],r
   cases=[c for c in read('cases.json') if c['case'] in next(g for g in read('groups.json') if g['id']==name)['cases']]
   for c in cases:print(extract(c),flush=True)
   pending.remove(name)
  save('results/pilot-collector-status.json',dict(pending=pending,updated=time.time()))
  if pending:time.sleep(40)
 save('results/pilot-summary.json',[read('data/fields/'+c['case']+'.json') for c in read('cases.json') if c['split']=='pilot'])
except Exception:
 (ROOT/'results/pilot-collector-error.txt').write_text(traceback.format_exc());raise
