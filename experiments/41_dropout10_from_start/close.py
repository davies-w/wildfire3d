"""Archive and close the diagnosed pre-training controller failure."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64,fcntl,shutil
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,B,BUCKET,PROJECT
O=R/'results';p=json.loads((O/'package.json').read_text());prefix=p['prefix'];assert json.loads((O/'collected.json').read_text())['passed']
e=json.loads((O/'execution.json').read_text())['name'];state=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1');assert state['state']=='SUCCEEDED'
assert json.loads(state['result'])['batch_state']=='SUCCEEDED'
inv={}
for c in p['candidates']:
 inv[c['id']]={k:gc(*v,'--filter=labels.trial_id='+c['label']) for k,v in dict(jobs=('batch','jobs','list','--location='+c['region']),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(inv[c['id']].values())
events=gc('logging','read','resource.type="gce_instance" AND protoPayload.resourceName:"fds-gpu41-pool01" AND (protoPayload.methodName:"compute.instances.insert" OR protoPayload.methodName:"compute.instances.delete")','--limit=10000');assert 0<len(events)<10000
starts={v['operation']['id'] for v in events if v.get('operation',{}).get('first') and v['protoPayload']['methodName'].endswith('.insert')};ends={v['operation']['id'] for v in events if v.get('operation',{}).get('last') and v['protoPayload']['methodName'].endswith('.insert')};assert starts<=ends,'Unresolved allocation'
records=json.loads((R.parents[1]/'docs/billing-audit-2026-10-23/vm-runtime.json').read_text());matched=[r for r in records if str(r.get('trial_id','')).startswith('gpu41-pool01')]
success=[v for v in events if v.get('operation',{}).get('last') and v['protoPayload']['methodName'].endswith('.insert') and not v['protoPayload'].get('status',{}).get('code')]
assert {v['protoPayload']['resourceName'].rsplit('/',1)[-1] for v in success}<={r['vm'] for r in matched}
c=json.loads((O/'read-condition.json').read_text())
if any(v.get('condition')==c for v in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings']):subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(O/'read-condition.json')],check=True,capture_output=True)
assert not any(v.get('condition')==c for v in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings'])
with (B.parent/'data/budget.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text())
 for candidate in p['candidates']:
  v=b['reservations']['dropout41-pool01-'+candidate['id']];cost=sum(x['estimated_compute_usd'] for x in matched if x['trial_id']==candidate['label']);v.update(state='completed_closed',cost=dict(stage='runtime_estimate',usd=cost),terminal_evidence='experiments/41_dropout10_from_start/results/pool-closed.json')
 b['reserved_usd']=sum(v['allowance_usd'] for v in b['reservations'].values() if v['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);B.write_text(json.dumps(b,indent=2)+'\n')
audit=dict(passed=True,reason='Batch succeeded and all selected/epoch artifacts verified',cleanup=inv,execution=state,allocation_events=events,measured_vm_records=matched,exact_grant_removed=c)
(O/'pool-closed.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(dict(passed=True,cost_estimate=sum(v['estimated_compute_usd'] for v in matched),total_with_other_reservations=b['estimated_spend_usd']+b['reserved_usd'])))
