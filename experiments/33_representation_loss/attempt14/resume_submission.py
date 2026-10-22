"""Resume first submission after oversized exact-file IAM condition failed.
No compute was submitted; retain the existing full reservation and immutable inputs.
Never use after a submitted/unknown execution outcome.
"""
import fcntl,datetime,subprocess,hashlib,yaml,shutil
from cloud import *
def main():
 with (R.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=read('budget.json');entry=b['reservations']['pilot14'];assert entry['state']=='reserved_before_upload';assert not (R/'results/execution.json').exists()
  assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu33-pilot14');assert not gc('compute','instances','list','--filter=labels.trial_id=gpu33-pilot14')
  assert hashlib.sha256((R/'data/pilot-overlay.tar').read_bytes()).hexdigest()==read('results/prepared.json')['overlay_sha256']
  groups=read('groups.json');assert all(g['phase'] in ['coverage','development'] for g in groups)
  allcases={c['case']:c for c in json.loads((R.parent.parent/'32_tree_expansion/cases.json').read_text())}
  assert all(allcases[n]['split']!='test' for g in groups for n in g['cases'])
  if not (R/'results/input-read-condition-exact-failed.json').exists():shutil.copy2(R/'results/input-read-condition.json',R/'results/input-read-condition-exact-failed.json')
  else:shutil.copy2(R/'results/input-read-condition.json',R/'results/input-read-condition-groups-failed.json')
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ');base='projects/_/buckets/'+BUCKET+'/objects/'
  allgroups=json.loads((R.parent.parent/'32_tree_expansion/groups.json').read_text())
  matched={g['id'] for g in allgroups if g['id'].startswith('x32-development-')}
  assert matched=={g['id'] for g in groups if g['phase']=='development'}
  coverage=[g['id'] for g in groups if g['phase']=='coverage'];assert len(coverage)==1
  prefixes=['expansion32/x32-development-','expansion32/'+coverage[0]+'/']
  clauses=['resource.name == '+json.dumps(base+'repair33/pilot14/pilot-overlay.tar')]+['resource.name.startsWith('+json.dumps(base+x)+')' for x in prefixes]
  condition=dict(title='exp33-pilot14-development-inputs',description='Temporary development-only group reads; all group members checked non-test',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/input-read-condition.json')],check=True)
  save('results/submission-recovery.json',dict(reason='Exact-file policy exceeded GCS policy size limit before any compute submission',existing_reservation_retained=True,development_groups=len(groups),all_group_members_non_test=True,scope='May read other development artifacts/seed replicas in these36 groups; no test groups or other prefixes'))
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-gpu33-pilot14','--location=us-central1','--source='+str(R/'gpu-workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-gpu33-pilot14','--location=us-central1')['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
  entry['state']='submission_pending';save('budget.json',b);e=gc('workflows','execute','fds-gpu33-pilot14','--location=us-central1');save('results/execution.json',e);entry.update(state='submitted',execution=e['name']);save('budget.json',b);print('SUBMITTED',e['name'])
if __name__=='__main__':main()
