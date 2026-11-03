"""Close only the archived, terminal stop diagnostic; retain pilot05's allowance."""
from cloud48_05 import *
import datetime
Q=R/'private-stopcheck01';W='fds-tree48-stopcheck01'
assert not (Q/'closed.json').exists()
assert json.loads((Q/'status.json').read_text())['state']=='FAILED'
a=json.loads((Q/'archive-proof.json').read_text());assert a['passed'] and len(a['objects'])==61
logs=json.loads((Q/'allocation-logs.json').read_text());vms={}
for x in logs:
 p=x.get('protoPayload',{});m=p.get('methodName','');op=x.get('operation',{})
 if '.instances.' not in m:continue
 n=p['resourceName'].split('/')[-1];assert n.startswith('fds-tree48-stopche-')
 v=vms.setdefault(n,{'start':[],'end':[]});t=datetime.datetime.fromisoformat(x['timestamp'].replace('Z','+00:00')).timestamp()
 if m.endswith('.insert') and op.get('first'):v['start'].append(t)
 if m.endswith('.delete') and op.get('last'):v['end'].append(t)
assert len(vms)==1 and all(v['start'] and v['end'] for v in vms.values())
seconds=sum(max(v['end'])-min(v['start']) for v in vms.values());cost=seconds/3600*.15
empty={k:gc(*args,'--filter=name~fds-tree48-stopche') for k,args in {'vms':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};assert not any(empty.values())
gc('storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(Q/'read-condition.json'))
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());old=b['reservations'][W];assert old['state']=='submitted';allowance=old['allowance_usd'];assert cost<allowance
 old.update(state='closed',cost={'usd':cost,'allocation_seconds':seconds,'rate_usd_per_hour':.15,'stage':'conservative_allocation_estimate'})
 b['estimated_spend_usd']+=cost;b['accounting']['spend_estimate_usd']=b['estimated_spend_usd'];b['reserved_usd']-=cost;b['reservations'][WF]['allowance_usd']+=allowance-cost
 B.write_text(json.dumps(b,indent=2)+'\n')
 (Q/'closed.json').write_text(json.dumps(dict(passed=True,empty=empty,grant_removed=True,allocation_seconds=seconds,compute_estimate_usd=cost,remainder_returned_to_pilot05=True),indent=2))
print('Terminal test closed; pilot05 grant untouched.')
