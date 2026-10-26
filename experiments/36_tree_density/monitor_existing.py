"""Collect existing executions only; never submit or retry compute."""
from pathlib import Path
import json,fcntl,time,subprocess,traceback
from cloud import R,G,BUCKET,active_groups,read,save,collect
with (R/'data/dispatcher.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  pending=[]
  for g in active_groups():
   n=g['id'];folder=R/'jobs'/n
   if not (folder/'execution.json').exists() or (folder/'completion.json').exists() or (folder/'terminal-no-results.json').exists():continue
   try:
    if not collect(n):pending.append(n)
   except Exception:
    status=read(f'jobs/{n}/status.json')
    if status['state']=='ACTIVE':raise
    p=folder/'recorded-job-status.json'
    subprocess.run([G,'storage','cp','gs://'+BUCKET+'/density36/'+n+'/job-status.json',str(p)],check=True,capture_output=True,timeout=120)
    job=json.loads(p.read_text());assert job['status'].get('runDuration')=='0s' and job['status']['state'] in ['SCHEDULED','QUEUED','SCHEDULED_PENDING_QUEUED'], 'Unexpected failure; investigate'
    assert not any(read(f'jobs/{n}/cleanup.json').values()) and read(f'jobs/{n}/permission-removed.json')['removed']
    save(f'jobs/{n}/terminal-no-results.json',dict(reason='Queue deadline after globalCPUquota rejection',run_duration_s=0,cleanup_verified=True,grant_removed=True,diagnosed=True))
    print('QUEUE_TIMEOUT_NO_RUN',n,flush=True)
  save('results/existing-monitor.json',dict(active=pending,submissions_enabled=False))
  if not pending:break
  time.sleep(60)
