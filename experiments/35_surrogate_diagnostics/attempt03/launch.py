import time,fcntl,hashlib,datetime,subprocess,yaml,sys,concurrent.futures
from cloud import *
def main():
 with (R.parent.parent/'33_representation_loss/data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert read('results/preflight.json')['passed']
  for n,h in read('results/input-freeze.json').items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
  assert not gc('compute','instances','list','--filter=labels.trial_id=gpu35-diag03')
  assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu35-diag03')
  ledger=read('budget.json')
  if 'diag35-03' in ledger['reservations']:
   assert '--recover-reserved-setup' in sys.argv
   assert ledger['reservations']['diag35-03']['state']=='reserved_before_upload'
   assert not (R/'results/execution.json').exists()
   assert not gc('workflows','list','--location=us-central1','--filter=name:fds-gpu35-diag03')
  else:
   assert ledger['reserved_usd']+4.5<=ledger['authorized_usd'];ledger['reserved_usd']=round(ledger['reserved_usd']+4.5,2);ledger['reservations']['diag35-03']=dict(state='reserved_before_upload',allowance_usd=4.5,reserved_unix=time.time(),compute_allowance_usd=1.6,ancillary_cleanup_allowance_usd=2.9);save('budget.json',ledger)
  # Restore only verified missing inputs, under a new immutable attempt prefix.
  def restore(item):
   source=R.parent.parent/'32_tree_expansion/data/cloud_archive'/item['archive_relative'];assert source.stat().st_size==item['bytes'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
   subprocess.run([G,'storage','cp','--if-generation-match=0',str(source),'gs://'+BUCKET+'/'+item['target']],check=True,capture_output=True)
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(restore,read('restore-manifest.json')))
  listings=subprocess.run([G,'storage','ls','--recursive','gs://'+BUCKET+'/diagnostics35/attempt03/restored/'],check=True,text=True,capture_output=True).stdout.splitlines();present=set(listings)
  for prefix in read('input-sources.json').values():
   for ext in ['.summary.json','.tar.gz']:assert 'gs://'+BUCKET+'/'+prefix+ext in present,(prefix,ext)
  save('results/input-availability.json',dict(passed=True,objects=2*len(read('input-sources.json')),restored=len(read('restore-manifest.json'))))
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/pilot-overlay.tar'),'gs://'+BUCKET+'/diagnostics35/attempt03/pilot-overlay.tar'],check=True)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
  base='projects/_/buckets/'+BUCKET+'/objects/'
  allgroups=json.loads((R.parent.parent/'32_tree_expansion/groups.json').read_text());allcases={c['case']:c for c in json.loads((R.parent.parent/'32_tree_expansion/cases.json').read_text())}
  prefixes=['expansion32/x32-development-','expansion32/x32-coverage-00-r1/']
  allowed=[g for g in allgroups if any(('expansion32/'+g['id']+'/').startswith(p) for p in prefixes)]
  assert all(allcases[n]['split']!='test' for g in allowed for n in g['cases'])
  assert {g['id'] for g in read('groups.json')} <= {g['id'] for g in allowed}
  assert all(v.startswith('diagnostics35/attempt03/restored/') for v in read('input-sources.json').values())
  clauses=['resource.name.startsWith('+json.dumps(base+'diagnostics35/attempt03/restored/')+')','resource.name == '+json.dumps(base+'diagnostics35/attempt03/pilot-overlay.tar')]
  condition=dict(title='exp35-diag03-fresh-inputs',description='24h fresh verified development48cases only; no old expiring prefixes',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-gpu35-diag03','--location=us-central1','--source='+str(R/'gpu-workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu35-diag03','--location=us-central1')['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
  ledger['reservations']['diag35-03']['state']='submission_pending';save('budget.json',ledger)
  e=gc('workflows','execute','fds-gpu35-diag03','--location=us-central1');save('results/execution.json',e);ledger['reservations']['diag35-03'].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('SUBMITTED',e['name'])
if __name__=='__main__':main()
