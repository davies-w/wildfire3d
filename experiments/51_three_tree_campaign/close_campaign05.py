"""Reconcile audited05 and transfer only its original remainder to unique06."""
from cloud05 import *
assert WF=='t51r05' and RESERVATION=='fds-tree51-campaign05' and not (P/'closed.json').exists()
assert json.loads((R/'private04/continuation-authorization.json').read_text())['rolling_fallback_authorized']
a=json.loads((P/'terminal-archive.json').read_text());assert a['passed'] and not any(a['empty'].values())
retired=json.loads((P/'grants-retired.json').read_text());assert retired['passed'] and retired['independent_policy_readback_verified']
v=json.loads((P/'allocation-summary.json').read_text());assert v['passed'] and v['pairs']==71 and not v['case71_vm_observed'] and not v['case71_batch_snapshot_observed']
pairs=json.loads((P/'terminal-runtime-pairs.json').read_text());assert {x['index'] for x in pairs.values()}==set(range(71))
proofs=json.loads((P/'terminal-batch-proofs.json').read_text());assert len(proofs)==71 and all(x['proof']['status']['state']=='SUCCEEDED' for x in proofs)
objects=json.loads((P/'terminal-objects.json').read_text());assert not any(x['name'].startswith(PREFIX+'wave-000071/') for x in objects)
assert not json.loads((P/'failed71-audit-logs.json').read_text())
assert all(x['state']!='ACTIVE' for x in json.loads((P/'case-executions.json').read_text()))
empty={k:gc(*args,'--filter=name~t51r05') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
seconds=sum(max(x['end'])-min(x['start']) for x in pairs.values());cost=seconds*.15/3600;assert cost==v['compute_upper_usd']
save('case71-eligibility.json',dict(passed=True,case='tree51_000273_baseline',classification='audited_failed_submission_without_observed_Batch_or_VM_allocation',no_case_outputs=True,full_allocation_indices=list(range(71)),prior_post_not_retried=True,eligible_for_one_new_unique_continuation_attempt=True,not_a_checkpoint_resume=True))
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());old=b['reservations'][RESERVATION];assert old['state']=='submitted';allowance=old['allowance_usd'];assert cost<allowance
 key='fds-tree51-campaign06';assert key not in b['reservations'];old.update(state='creation502_audited_closed',cost=dict(usd=cost,allocation_seconds=seconds,rate_usd_per_hour=.15,stage='conservative_allocation_estimate'))
 b['estimated_spend_usd']+=cost;b['accounting']['spend_estimate_usd']=b['estimated_spend_usd'];b['reserved_usd']-=cost;b['reservations'][key]=dict(state='reserved_before_upload',allowance_usd=allowance-cost,reserved_unix=time.time(),scope='Only audited original rolling remainder; remaining eligible cases and ancillary costs; no added allowance')
 assert b['reservations']['fds-tree51-training']['allowance_usd']==20 and b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200
 B.write_text(json.dumps(b,indent=2)+'\n');save('closed.json',dict(passed=True,empty=empty,four_exact_grants_removed=True,allocation_seconds=seconds,compute_estimate_usd=cost,remainder_reserved_to=key,remaining_allowance_usd=allowance-cost,training_reserve_untouched=True,accepted_cases=295))
print('Closed05; original remainder reserved06; no new simulation submitted')
