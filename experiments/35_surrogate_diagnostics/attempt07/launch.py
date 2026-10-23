import time,fcntl,hashlib,datetime,subprocess,yaml,sys,concurrent.futures
from cloud import *
def main():
 with (R.parent.parent/'33_representation_loss/data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert read('results/preflight.json')['passed']
  for n,h in read('results/input-freeze.json').items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
  assert not gc('compute','instances','list','--filter=labels.trial_id=gpu35-hot07')
  assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu35-hot07')
  ledger=read('budget.json')
  if 'hot35-07' in ledger['reservations']:
   assert '--recover-reserved-setup' in sys.argv
   assert ledger['reservations']['hot35-07']['state']=='reserved_before_upload'
   assert not (R/'results/execution.json').exists()
   assert not gc('workflows','list','--location=us-central1','--filter=name:fds-gpu35-hot07')
  else:
   assert ledger['reserved_usd']+12<=ledger['authorized_usd'];ledger['reserved_usd']=round(ledger['reserved_usd']+12,2);ledger['reservations']['hot35-07']=dict(state='reserved_before_upload',allowance_usd=12,reserved_unix=time.time(),compute_allowance_usd=7,ancillary_cleanup_allowance_usd=5);save('budget.json',ledger)
  save('results/input-availability.json',dict(passed=True,scope='Frozen decoded local training trajectory included in hash-verified overlay'))
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/pilot-overlay.tar'),'gs://'+BUCKET+'/diagnostics35/attempt07/pilot-overlay.tar'],check=True)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
  base='projects/_/buckets/'+BUCKET+'/objects/'
  clauses=['resource.name == '+json.dumps(base+'diagnostics35/attempt07/pilot-overlay.tar')]
  condition=dict(title='exp35-hot07-inputs',description='24h exact verified 400-trajectory package only',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-gpu35-hot07','--location=us-central1','--source='+str(R/'gpu-workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu35-hot07','--location=us-central1')['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
  ledger['reservations']['hot35-07']['state']='submission_pending';save('budget.json',ledger)
  e=gc('workflows','execute','fds-gpu35-hot07','--location=us-central1');save('results/execution.json',e);ledger['reservations']['hot35-07'].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('SUBMITTED',e['name'])
if __name__=='__main__':main()
