"""Release old quota-rejected allowances only with live and allocation evidence."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime,fcntl,json,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,G,PROJECT,BUCKET,gc,read,save
keys=[f'x36-density-{i:03}' for i in range(9,21)]
query='resource.type="gce_instance" AND (protoPayload.methodName="v1.compute.instances.insert" OR protoPayload.methodName="v1.compute.instances.delete") AND timestamp>="2026-10-15T00:00:00Z"'
events=gc('logging','read',query,'--limit=5000');assert len(events)<5000
inventory={k:gc(*cmd) for k,cmd in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
policy=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)
def verify(key):
    prior=read('jobs/'+key+'/status.json');x=prior['name'].split('/');live=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');assert live['state']!='ACTIVE' and live['name']==prior['name'];result=json.loads(live['result']);record=read('jobs/'+key+'/recorded-job-status.json');uid=record['uid'];assert result['job_uid']==uid and result['workers_remaining']==0 and result['final_state'] in ['SCHEDULED','QUEUED'];assert record['status']['runDuration']=='0s' and record['status'].get('taskGroups',{}).get('group0',{}).get('counts',{}) in [{'PENDING':'1'},{}];assert any('CODE_GCE_QUOTA_EXCEEDED' in e.get('description','') for e in record['status']['statusEvents']);assert read('jobs/'+key+'/terminal-no-results.json')['reason']=='Queue deadline after globalCPUquota rejection';assert read('jobs/'+key+'/cleanup.json')=={'instances':[],'disks':[],'jobs':[]}
    assert not any(' to RUNNING ' in e.get('description','') for e in record['status']['statusEvents'])
    allocation=[e for e in events if uid in e.get('protoPayload',{}).get('resourceName','')];success=[e for e in allocation if e.get('operation',{}).get('last') and e['protoPayload']['methodName'].endswith('.insert') and not e['protoPayload'].get('status',{}).get('code')];assert not success
    for kind,items in inventory.items():assert not any(uid in v.get('name','') or v.get('labels',{}).get('trial_id')==key for v in items),(key,kind)
    condition=read('jobs/'+key+'/read-condition.json');assert not any(b.get('condition')==condition for b in policy.get('bindings',[]))
    return dict(key=key,execution=live,job_uid=uid,quota_rejection_record=record['status'],matching_allocation_events=allocation,successful_vm_allocations=0,live_resources_empty=True,exact_temporary_read_grant_absent=True)
with ThreadPoolExecutor(max_workers=4) as pool:proofs=list(pool.map(verify,keys))
with (B.parent/'data/budget.lock').open('w') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX);budget=json.loads(B.read_text());released=0
    for proof in proofs:
        r=budget['reservations'][proof['key']];assert r['execution']==proof['execution']['name'] and r['state'] in ['submitted','completed_reconciled']
        if r['state']=='submitted':released+=r['allowance_usd']
        r.update(state='completed_reconciled',historical_allowance_usd=r['allowance_usd'],terminal_evidence='experiments/36_tree_density/results/unallocated-cpu-reconciliation.json',cost=dict(stage='verified_no_vm_allocation',usd=0,scope='Zero VM compute allocation proven from quota-rejected pending task plus complete successful-insert audit. Shared storage/workflow charges remain project-level; this is not a zero invoice claim.'))
    budget['reserved_usd']=sum(v['allowance_usd'] for v in budget['reservations'].values() if v['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);assert budget['estimated_spend_usd']+budget['reserved_usd']<=budget['authorized_usd'];B.write_text(json.dumps(budget,indent=2)+'\n')
save('results/unallocated-cpu-reconciliation.json',dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),logging_query=query,allocation_events_examined=len(events),allowance_released_this_invocation_usd=released,proofs=proofs,estimated_spend_usd=budget['estimated_spend_usd'],reserved_usd=budget['reserved_usd'],headroom_usd=budget['authorized_usd']-budget['estimated_spend_usd']-budget['reserved_usd'],scope='Original twelve quota-rejected executions only. Replacement execution costs are not released or relabeled. No compute, solver, queue or Flex job changed.'))
print(json.dumps(dict(passed=True,released_usd=released,reserved_usd=budget['reserved_usd'],headroom_usd=budget['authorized_usd']-budget['estimated_spend_usd']-budget['reserved_usd'])))
