"""Close terminal compact01 after full immutable-object and VM-runtime verification."""
from cloud import *
assert not (P/'closed.json').exists()
a=json.loads((P/'terminal-archive.json').read_text());assert a['passed'] and len(a['objects'])==437 and not any(a['empty'].values())
status=json.loads((P/'status.json').read_text());assert status['controller']['state']=='SUCCEEDED' and not status['jobs'] and not status['vms']
assert all(x['proof']['status']['state']=='SUCCEEDED' for x in json.loads((P/'terminal-batch-proofs.json').read_text()))
vms=json.loads((P/'terminal-runtime-pairs.json').read_text());assert len(vms)==22 and all(v['start'] and v['end'] for v in vms.values())
seconds=sum(max(v['end'])-min(v['start']) for v in vms.values());cost=seconds/3600*.15
empty={k:gc(*args,'--filter=name~fds-tree49-compact') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
gc('storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'read-condition.json'))
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());old=b['reservations'][WF];assert old['state']=='submitted';allowance=old['allowance_usd'];assert cost<allowance
 key='fds-tree49-artifact-accounting';assert key not in b['reservations']
 old.update(state='terminal_closed',cost={'usd':cost,'allocation_seconds':seconds,'rate_usd_per_hour':.15,'stage':'conservative_allocation_estimate'})
 b['estimated_spend_usd']+=cost;b['accounting']['spend_estimate_usd']=b['estimated_spend_usd'];b['reserved_usd']-=cost
 b['reservations'][key]=dict(state='reserved_pending_shared_costs',allowance_usd=allowance-cost,reserved_unix=time.time(),scope='Unspent original pilot allowance retained only for pending shared/build/transfer/storage costs; all22 retained solves complete; no new solver authorization')
 assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
 B.write_text(json.dumps(b,indent=2)+'\n');save('closed.json',dict(passed=True,empty=empty,grant_removed=True,allocation_seconds=seconds,compute_estimate_usd=cost,remainder_reserved_for_pending_shared_costs=True))
print('Compact01 closed; original remainder retained for pending shared costs only.')
