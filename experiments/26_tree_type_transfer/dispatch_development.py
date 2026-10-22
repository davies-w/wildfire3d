"""Submit remaining approved development groups when slots free; never tests/retries."""
import fcntl,time,json
from cloud import ROOT,gc,launch,read,save
lock=(ROOT/'data/development-dispatch.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
end=time.time()+3*3600
for name in ['t26-development-3','t26-development-4','t26-development-7']:
 while time.time()<end:
  ledger=read('budget.json')
  if name in ledger['reservations']:
   assert (ROOT/'jobs'/name/'execution.json').exists(),'Reserved but submission uncertain; do not retry'
   break
  vms=gc('compute','instances','list');jobs=gc('batch','jobs','list','--location=us-central1')
  if len(vms)>=6 or len(jobs)>=6:time.sleep(40);continue
  launch(name,2.2);break
 else:raise SystemExit('Dispatch deadline expired; no additional jobs submitted')
print('ALL DEVELOPMENT SUBMITTED',flush=True)
