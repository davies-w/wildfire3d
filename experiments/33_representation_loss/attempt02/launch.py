import time,fcntl,hashlib,datetime,subprocess,yaml
from cloud import *
def main():
 with (R.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert read('results/preflight.json')['passed']
  for n,h in read('results/input-freeze.json').items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
  assert not gc('compute','instances','list','--filter=labels.trial_id=gpu33-pilot02')
  assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu33-pilot02')
  ledger=read('budget.json');assert 'pilot02' not in ledger['reservations'];assert ledger['reserved_usd']+1.5<=ledger['authorized_usd']
  ledger['reserved_usd']=round(ledger['reserved_usd']+1.5,2);ledger['reservations']['pilot02']=dict(state='reserved_before_upload',allowance_usd=1.5,reserved_unix=time.time(),compute_allowance_usd=1.2,ancillary_cleanup_allowance_usd=.3);save('budget.json',ledger)
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/pilot-overlay.tar'),'gs://'+BUCKET+'/repair33/pilot02/pilot-overlay.tar'],check=True)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
  base='projects/_/buckets/'+BUCKET+'/objects/';objects=['repair33/pilot02/pilot-overlay.tar']
  for c in read('cases.json'):
   group=next(g['id'] for g in read('groups.json') if c['case'] in g['cases'])
   objects.extend('expansion32/'+group+'/'+c['case']+suffix for suffix in ['.tar.gz','.summary.json'])
  # Exact objects, no access to fresh tests or unrelated bucket content.
  expression="request.time < timestamp('"+expiry+"') && resource.name in "+json.dumps([base+x for x in objects])
  condition=dict(title='exp33-pilot-inputs',description='Temporary exact development inputs for approved model repair',expression=expression);save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-gpu33-pilot02','--location=us-central1','--source='+str(R/'gpu-workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu33-pilot02','--location=us-central1')['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
  ledger['reservations']['pilot02']['state']='submission_pending';save('budget.json',ledger)
  e=gc('workflows','execute','fds-gpu33-pilot02','--location=us-central1');save('results/execution.json',e);ledger['reservations']['pilot02'].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('SUBMITTED',e['name'])
if __name__=='__main__':main()
