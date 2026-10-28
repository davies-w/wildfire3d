"""Close the exact capacity-limited canonical01 reservation after proof of no VM allocation."""
from pathlib import Path
import datetime,fcntl,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,gc,read,save
KEY='density36-canonical-pilot01'
collected=read('results/canonical-pilot01-collected.json');assert not collected['experiment_complete'] and collected['cleanup_verified']
execution=read('results/canonical-pilot01-execution.json')['name'];x=execution.split('/');live=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');assert live['state']!='ACTIVE'
assert read('results/canonical-pilot01-permission-removed.json')['exact_grant_removed']
assert read('results/canonical-pilot01-cleanup.json')=={'jobs':[],'instances':[],'disks':[]}
for cmd in [('batch','jobs','list','--location=us-east4'),('compute','instances','list'),('compute','disks','list')]:assert not gc(*cmd,'--filter=labels.trial_id=gpu36-canonical01')
record=json.loads((R/'data/canonical-pilot01-results/job-status.json').read_text());uid=record['uid'];status=record['status'];assert status['state'] in ['QUEUED','SCHEDULED','DELETION_IN_PROGRESS'];assert status['runDuration']=='0s';assert status.get('taskGroups',{}).get('group0',{}).get('counts',{}) in [{},{'PENDING':'1'}]
assert not any(' to RUNNING ' in e.get('description','') for e in status.get('statusEvents',[]))
query='protoPayload.methodName="v1.compute.instances.insert" AND protoPayload.resourceName:"'+uid+'" AND timestamp>="'+live['startTime']+'"'
events=gc('logging','read',query,'--limit=5000');assert len(events)<5000
completed=[e for e in events if e.get('operation',{}).get('last')]
operations={e.get('operation',{}).get('id') for e in events};finished={e.get('operation',{}).get('id') for e in completed};assert None not in operations and operations<=finished,'An insertion has no terminal audit record; wait, do not assume zero compute'
assert all(e['protoPayload'].get('status',{}).get('code') for e in completed),'A successful insertion forbids zero-compute reconciliation'
# A pending job alone cannot prove zero compute. Require explicit stockout plus terminal failed insertions.
assert any('CODE_GCE_ZONE_RESOURCE_POOL_EXHAUSTED' in e.get('description','') for e in status.get('statusEvents',[]))
assert completed, 'Missing insertion audit evidence; wait rather than claiming zero compute'
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());r=b['reservations'][KEY];assert r['execution']==execution and r['state'] in ['submitted','completed_reconciled'];r.update(state='completed_reconciled',historical_allowance_usd=r['allowance_usd'],terminal_evidence='experiments/36_tree_density/results/canonical-pilot01-cost-reconciled.json',cost={'stage':'verified_no_vm_allocation','usd':0,'scope':'Zero VM compute allocated; shared workflow/storage charges remain project-level. Not a zero invoice claim.'});b['reserved_usd']=sum(v['allowance_usd'] for v in b['reservations'].values() if v['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd'];B.write_text(json.dumps(b,indent=2)+'\n')
proof=dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution=live,recorded_job_status=record,query=query,allocation_events=events,successful_vm_allocations=0,pilot_compute_cost=r['cost'],estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],headroom_usd=b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd'])
save('results/canonical-pilot01-no-allocation-proof.json',proof);save('results/canonical-pilot01-cost-reconciled.json',proof);print(json.dumps({k:proof[k] for k in ['passed','pilot_compute_cost','reserved_usd','headroom_usd']}))
