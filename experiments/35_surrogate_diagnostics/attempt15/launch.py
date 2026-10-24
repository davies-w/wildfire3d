import time,fcntl,hashlib,datetime,subprocess,yaml,sys,concurrent.futures
from cloud import *
def main():
 with (R.parent.parent/'33_representation_loss/data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert read('results/preflight.json')['passed']
  for n,h in read('results/input-freeze.json').items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
  assert not gc('compute','instances','list','--filter=labels.trial_id=gpu35-min15')
  assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu35-min15')
  ledger=read('budget.json')
  if 'min35-15' in ledger['reservations']:
   assert '--recover-reserved-setup' in sys.argv
   assert ledger['reservations']['min35-15']['state']=='reserved_before_upload'
   assert not (R/'results/execution.json').exists()
   assert not gc('workflows','list','--location=us-central1','--filter=name:fds-gpu35-min15')
  else:
   assert ledger['estimated_spend_usd']+ledger['reserved_usd']+3<=ledger['authorized_usd'];ledger['reserved_usd']=round(ledger['reserved_usd']+3,2);ledger['reservations']['min35-15']=dict(state='reserved_before_upload',allowance_usd=3,reserved_unix=time.time(),compute_allowance_usd=2.2,ancillary_cleanup_allowance_usd=.8,cost=dict(stage='pre_run_estimate',expected_usd=[.5,1.2]));save('budget.json',ledger)
  save('results/input-availability.json',dict(passed=True,scope='Frozen decoded development trajectories included in hash-verified overlay'))
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/pilot-overlay.tar'),'gs://'+BUCKET+'/diagnostics35/attempt15/pilot-overlay.tar'],check=True)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
  base='projects/_/buckets/'+BUCKET+'/objects/'
  clauses=['resource.name == '+json.dumps(base+'diagnostics35/attempt15/pilot-overlay.tar')]
  condition=dict(title='exp35-min15-inputs',description='24h exact verified 520-history minimal-material sequence package only',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-gpu35-min15','--location=us-central1','--source='+str(R/'gpu-workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu35-min15','--location=us-central1')['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
  ledger['reservations']['min35-15']['state']='submission_pending';save('budget.json',ledger)
  e=gc('workflows','execute','fds-gpu35-min15','--location=us-central1');save('results/execution.json',e);ledger['reservations']['min35-15'].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('SUBMITTED',e['name'])
if __name__=='__main__':main()
