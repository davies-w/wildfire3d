"""One locked collector; downloads evidence and removes exact temporary grant."""
import fcntl,time,hashlib,subprocess
from cloud import *
def main():
 with (R/'data/collector.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  eid=read('results/execution.json')['name'].split('/')[-1]
  while True:
   state=gc('workflows','executions','describe',eid,'--workflow=fds-gpu35-diag06','--location=us-central1');save('results/status.json',state)
   if state['state']!='ACTIVE':break
   time.sleep(45)
  inv={k:gc(*args,'--filter=labels.trial_id=gpu35-diag06') for k,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};save('results/cleanup-first-observation.json',inv)
  for _ in range(12):
   if not any(inv.values()):break
   time.sleep(10)
   inv={k:gc(*args,'--filter=labels.trial_id=gpu35-diag06') for k,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
  save('results/cleanup.json',inv);assert not any(inv.values()),'cleanup incomplete'
  # gcloud cp wildcard retains all partial checkpoints, even on a failed job.
  dest=R/'data/collected';dest.mkdir(exist_ok=True)
  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt06/*.json',str(dest)],check=True)
  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt06/*.pt',str(dest)],check=False)
  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt06/projections.npz',str(dest)],check=False)
  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt06/bootstrap-error.txt',str(dest)],check=False)
  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt06/error.txt',str(dest)],check=False)
  subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
  save('results/permission-removed.json',dict(removed=True,time_unix=time.time()))
  with (R.parent.parent/'33_representation_loss/data/budget.lock').open('w') as f:
   fcntl.flock(f,fcntl.LOCK_EX);b=read('budget.json');b['reservations']['diag35-06'].update(state='terminal_cleanup_verified',completed_unix=time.time());save('budget.json',b)
  if (dest/'complete.json').exists():
   done=json.loads((dest/'complete.json').read_text());assert done['success'];assert hashlib.sha256((dest/'report.json').read_bytes()).hexdigest()==done['report_sha256'];save('results/report.json',json.loads((dest/'report.json').read_text()));save('results/collected.json',dict(complete=True,cleanup_verified=True))
  else:save('results/collection-error.json',dict(workflow_state=state['state'],error=(dest/'error.txt').read_text() if (dest/'error.txt').exists() else 'No completion marker; inspect cloud logs',cleanup_verified=True))
if __name__=='__main__':main()
