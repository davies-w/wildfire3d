"""Retrieve report/projections, verify cleanup and revoke only this campaign's temporary read grant."""
from pathlib import Path
import json,time,fcntl,subprocess,hashlib
from cloud import gc,read,save,G,PROJECT
R=Path(__file__).parent
with (R/'data/evaluation-collector.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 e=read('results/evaluation-execution.json')['name'].split('/')[-1];s=gc('workflows','executions','describe',e,'--workflow=fds-gpu32-evaluation01','--location=us-central1');save('results/evaluation-status.json',s)
 if s['state']=='ACTIVE':print('ACTIVE');raise SystemExit(0)
 inv={k:gc(*a,'--filter=labels.trial_id=gpu32-evaluation01') for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};save('results/evaluation-cleanup.json',inv);assert not any(inv.values())
 dest=R/'data/evaluation';dest.mkdir(exist_ok=True)
 for n in ['complete.json','fresh-test-evaluation.json']:
  if not (dest/n).exists():subprocess.run([G,'storage','cp','gs://'+PROJECT+'-trial/expansion32/evaluation01/'+n,str(dest/n)],check=True)
 done=json.loads((dest/'complete.json').read_text());raw=(dest/'fresh-test-evaluation.json').read_bytes();assert done['success'] and hashlib.sha256(raw).hexdigest()==done['report_sha256'];report=json.loads(raw)
 for n in report['projections']:
  p=dest/('projection-'+n+'.npz')
  if not p.exists():subprocess.run([G,'storage','cp','gs://'+PROJECT+'-trial/expansion32/evaluation01/'+p.name,str(p)],check=True)
 (R/'results/fresh-test-evaluation.json').write_bytes(raw)
 with (R/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);ledger=read('budget.json');ledger['reservations']['gpu-evaluation-01'].update(state='terminal_cleanup_verified',completed_unix=time.time());save('budget.json',ledger)
 subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+PROJECT+'-trial','--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
 save('results/evaluation-collected.json',dict(complete=True,temporary_read_grant_removed=True,time_unix=time.time()));print('EVALUATION_COLLECTED')
