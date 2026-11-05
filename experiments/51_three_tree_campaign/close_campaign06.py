"""Reconcile audited06 and transfer only its original remainder to unique07."""
from cloud06 import *
assert WF=='t51r06' and RESERVATION=='fds-tree51-campaign06' and not (P/'closed.json').exists()
assert json.loads((R/'private04/continuation-authorization.json').read_text())['rolling_fallback_authorized']
a=json.loads((P/'terminal-archive.json').read_text());assert a['passed'] and not any(a['empty'].values())
retired=json.loads((P/'grants-retired.json').read_text());assert retired['passed'] and retired['independent_policy_readback_verified']
v=json.loads((P/'allocation-summary.json').read_text());assert v['passed'] and v['pairs']==176
pairs=json.loads((P/'terminal-runtime-pairs.json').read_text());assert {x['index'] for x in pairs.values()}==set(range(176))
proofs=json.loads((P/'terminal-batch-proofs.json').read_text());passed=[x for x in proofs if x['proof']['status']['state']=='SUCCEEDED'];assert len(passed)==173
assert {x['index'] for x in proofs if x['proof']['status']['state']!='SUCCEEDED'}=={12,17,171}
assert all(x['state']!='ACTIVE' for x in json.loads((P/'case-executions.json').read_text()))
empty={k:gc(*args,'--filter=name~t51r06') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
seconds=sum(max(x['end'])-min(x['start']) for x in pairs.values());cost=seconds*.15/3600;assert cost==v['compute_upper_usd']
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());old=b['reservations'][RESERVATION];assert old['state']=='submitted';allowance=old['allowance_usd'];assert cost<allowance
 key='fds-tree51-campaign07';assert key not in b['reservations'];old.update(state='monitoring_write_failure_audited_closed',cost=dict(usd=cost,allocation_seconds=seconds,rate_usd_per_hour=.15,stage='conservative_allocation_estimate'))
 b['estimated_spend_usd']+=cost;b['accounting']['spend_estimate_usd']=b['estimated_spend_usd'];b['reserved_usd']-=cost;b['reservations'][key]=dict(state='reserved_before_upload',allowance_usd=allowance-cost,reserved_unix=time.time(),scope='Only audited original rolling remainder; remaining eligible cases and ancillary costs; no added allowance')
 assert b['reservations']['fds-tree51-training']['allowance_usd']==20 and b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200
 B.write_text(json.dumps(b,indent=2)+'\n');save('closed.json',dict(passed=True,empty=empty,four_exact_grants_removed=True,allocation_seconds=seconds,compute_estimate_usd=cost,remainder_reserved_to=key,remaining_allowance_usd=allowance-cost,training_reserve_untouched=True,accepted_cases=468,pending_interrupted_review=[12,17,171]))
print('Closed06; original remainder reserved07; no new simulation submitted')
