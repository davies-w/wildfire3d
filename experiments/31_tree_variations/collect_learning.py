from pathlib import Path
import json,time,fcntl,subprocess
from cloud import gc,read,save,G,PROJECT
R=Path(__file__).parent
with (R/'data/gpu-collector.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  e=read('results/gpu-execution.json')['name'].split('/')[-1];s=gc('workflows','executions','describe',e,'--workflow=fds-gpu31-learning01','--location=us-central1');save('results/gpu-status.json',s)
  if s['state']=='ACTIVE':time.sleep(45);continue
  inv={k:gc(*a,'--filter=labels.trial_id=gpu31-learning01') for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};save('results/gpu-cleanup.json',inv)
  if any(inv.values()):time.sleep(30);continue
  dest=R/'data/gpu/cloud';dest.mkdir(parents=True,exist_ok=True);urls=subprocess.check_output([G,'storage','ls','gs://'+PROJECT+'-trial/variation31/gpu01/'],text=True).splitlines();urls=[u for u in urls if not u.endswith('/learning-overlay.tar')];subprocess.run([G,'storage','cp',*urls,str(dest)],check=True)
  with (R/'data/budget.lock').open('w') as f:
   fcntl.flock(f,fcntl.LOCK_EX);ledger=read('budget.json');ledger['reservations']['gpu-learning-01'].update(state='terminal_cleanup_verified',completed_unix=time.time());save('budget.json',ledger)
  print('GPU_COLLECTED',s['state'],flush=True);break
