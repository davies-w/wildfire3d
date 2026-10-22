import time,fcntl,hashlib,datetime,subprocess,yaml
from cloud import *
def main():
 with (R.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert read('results/preflight.json')['passed']
  for n,h in read('results/input-freeze.json').items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
  assert not gc('compute','instances','list','--filter=labels.trial_id=gpu33-pilot16')
  assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu33-pilot16')
  ledger=read('budget.json');assert 'pilot16' not in ledger['reservations'];assert ledger['reserved_usd']+4.5<=ledger['authorized_usd']
  ledger['reserved_usd']=round(ledger['reserved_usd']+4.5,2);ledger['reservations']['pilot16']=dict(state='reserved_before_upload',allowance_usd=4.5,reserved_unix=time.time(),compute_allowance_usd=1.6,ancillary_cleanup_allowance_usd=2.9);save('budget.json',ledger)
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/pilot-overlay.tar'),'gs://'+BUCKET+'/repair33/pilot16/pilot-overlay.tar'],check=True)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
  base='projects/_/buckets/'+BUCKET+'/objects/'
  allgroups=json.loads((R.parent.parent/'32_tree_expansion/groups.json').read_text());allcases={c['case']:c for c in json.loads((R.parent.parent/'32_tree_expansion/cases.json').read_text())}
  prefixes=['expansion32/x32-development-','expansion32/x32-coverage-00-r1/']
  allowed=[g for g in allgroups if any(('expansion32/'+g['id']+'/').startswith(p) for p in prefixes)]
  assert all(allcases[n]['split']!='test' for g in allowed for n in g['cases'])
  assert {g['id'] for g in read('groups.json')} <= {g['id'] for g in allowed}
  clauses=['resource.name == '+json.dumps(base+'repair33/pilot16/pilot-overlay.tar')]+['resource.name.startsWith('+json.dumps(base+p)+')' for p in prefixes]
  condition=dict(title='exp33-pilot16-development-inputs',description='24h development-only prefixes; group members verified non-test',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-gpu33-pilot16','--location=us-central1','--source='+str(R/'gpu-workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu33-pilot16','--location=us-central1')['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
  ledger['reservations']['pilot16']['state']='submission_pending';save('budget.json',ledger)
  e=gc('workflows','execute','fds-gpu33-pilot16','--location=us-central1');save('results/execution.json',e);ledger['reservations']['pilot16'].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('SUBMITTED',e['name'])
if __name__=='__main__':main()
