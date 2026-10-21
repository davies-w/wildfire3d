"""Launch cloud fitting only after all development cases pass; no automatic retry."""
import json,time,fcntl,subprocess,hashlib,yaml,datetime
from pathlib import Path
from cloud import gc,read,save,G,PROJECT
R=Path(__file__).parent
BUCKET='tmrw-wildfire-20261015-trial'
def main():
 with (R/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert read('results/development-complete.json')['complete']
  for g in read('groups.json'):
   if g['phase']!='test':assert read(f"jobs/{g['id']}/completion.json")['all_full_horizon']
  assert read('results/learning-interface-check.json')['passed']
  for n,h in read('results/learning-input-freeze.json').items():
   p=R/('development.json' if n=='cases.json' else n);digest=hashlib.sha256()
   with p.open('rb') as f:
    for chunk in iter(lambda:f.read(8*1024**2),b''):digest.update(chunk)
   assert digest.hexdigest()==h, 'Training package stale: '+n
  assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1')
  ledger=read('budget.json');key='gpu-learning-01';assert key not in ledger['reservations'];assert ledger['reserved_usd']+2.5<=ledger['authorized_usd']
  # Make the prepared package immutable; preserve uncertainty rather than replacing uploads.
  object_uri='gs://'+BUCKET+'/expansion32/gpu01/learning-overlay.tar'
  marker=R/'results/learning-overlay-upload.json'
  if not marker.exists():
   subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/learning-overlay.tar'),object_uri],check=True)
   save('results/learning-overlay-upload.json',gc('storage','objects','describe',object_uri))
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
  condition={'title':'exp32-inputs-read','description':'Temporary read for approved expanded training data','expression':"request.time < timestamp('"+expiry+"') && (resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/expansion32/') || resource.name == 'projects/_/buckets/"+BUCKET+"/objects/gpu29/train01/inputs.tar')"}
  cp=R/'results/input-read-condition.json';save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(cp)],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];f=R/'gpu-workflow.yaml'
  gc('workflows','deploy','fds-gpu32-learning01','--location=us-central1','--source='+str(f),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu32-learning01','--location=us-central1')['sourceContents'])==yaml.safe_load(f.read_text())
  ledger['reserved_usd']=round(ledger['reserved_usd']+2.5,4);ledger['reservations'][key]=dict(state='reserved',allowance_usd=2.5,reserved_unix=time.time(),vm_age_limit_s=9000,absolute_limit_s=10800,retries=0);save('budget.json',ledger)
  e=gc('workflows','execute','fds-gpu32-learning01','--location=us-central1');save('results/gpu-execution.json',e);ledger['reservations'][key].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('GPU_SUBMITTED',flush=True)
if __name__=='__main__':main()
