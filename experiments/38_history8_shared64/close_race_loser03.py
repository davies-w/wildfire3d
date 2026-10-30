"""Close only the verified unallocated Oregon loser of the user-authorized regional race."""
from pathlib import Path
import json,sys,fcntl,subprocess,datetime
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,B,BUCKET,PROJECT
O=R/'results03'
def save(n,x):(O/n).write_text(json.dumps(x,indent=2)+'\n')
winner=json.loads((R/'results04/race-winner.json').read_text());assert winner['winner']=='history38-training04' and winner['oregon_cleanup_verified']
prior=json.loads((R/'results04/oregon-before-cancellation.json').read_text());assert prior['status']['runDuration']=='0s'
e=json.loads((O/'execution.json').read_text())['name'];s=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow=fds-gpu38-history03','--location=us-central1');assert s['state'] not in ['ACTIVE','QUEUED']
inv={k:gc(*v,'--filter=labels.trial_id=gpu38-history03') for k,v in {'jobs':('batch','jobs','list','--location=us-west1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inv.values()),inv
query='resource.type="gce_instance" AND protoPayload.methodName:"compute.instances.insert" AND protoPayload.resourceName:"'+prior['uid']+'" AND timestamp>="'+prior['createTime']+'"'
events=gc('logging','read',query,'--limit=10000');assert 0<len(events)<10000
final=[x for x in events if x.get('operation',{}).get('last')];assert final,'No completed allocation audit events'
assert all(x['protoPayload'].get('status',{}).get('code',0)!=0 for x in final),'Successful VM allocation requires measured cost, not zero-cost closure'
initial_ids={x['operation']['id'] for x in events if x.get('operation',{}).get('first')};final_ids={x['operation']['id'] for x in final};assert initial_ids<=final_ids,'An allocation attempt lacks terminal audit evidence'
audit=dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='Iowa won authorized regional race',winner=winner,original_job=prior,workflow=s,cleanup=inv,allocation_events=events,completed_failed_allocations=len(final),successful_allocations=0,zero_vm_compute_verified=True)
save('race-cancellation-audit.json',audit)
c=json.loads((O/'read-condition.json').read_text());assert c['title']=='history38-training03-read'
bindings=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings']
if any(x.get('condition')==c for x in bindings):subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(O/'read-condition.json')],check=True,capture_output=True)
assert not any(x.get('condition')==c for x in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings'])
with (B.parent/'data/budget.lock').open('a') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());v=b['reservations']['history38-training03'];assert v['state'] in ['submitted','race_loser_cancelled']
 v.update(state='race_loser_cancelled',historical_allowance_usd=v['allowance_usd'],terminal_evidence='experiments/38_history8_shared64/results03/race-cancellation-audit.json',cost=dict(stage='verified_no_vm_allocation',usd=0,scope='All successful-insert completion audit events absent; all recorded allocation attempts failed, terminal job/VM/disks empty. Shared orchestration/storage charges remain project-level; not zero invoice.'))
 b['reserved_usd']=sum(x['allowance_usd'] for x in b['reservations'].values() if x['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);B.write_text(json.dumps(b,indent=2)+'\n')
save('race-closed.json',dict(passed=True,removed_exact_condition=c,reservation_released=17.7,estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],total=b['estimated_spend_usd']+b['reserved_usd'],raw_and_checkpoints_preserved=True))
print(json.dumps(dict(passed=True,failed_allocations=len(final),zero_vm_compute=True,reservation_released=17.7,total=b['estimated_spend_usd']+b['reserved_usd'])))
