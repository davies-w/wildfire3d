"""Close only terminal campaign04 after pinned archives and all allocation pairs pass."""
from cloud04 import *
assert WF=='fds-tree51-campaign04' and P.name=='private04'
assert json.loads((P/'continuation-authorization.json').read_text())['rolling_fallback_authorized'] is True
assert not (P/'closed.json').exists(),'Already closed; never repeat'
a=json.loads((P/'terminal-archive.json').read_text());assert a['passed'] and len(a['objects'])==len(json.loads((P/'terminal-objects.json').read_text())) and not any(a['empty'].values())
st=json.loads((P/'status.json').read_text());assert st['controller']['state']=='FAILED'
assert 'Child failed' in st['controller']['error']['payload']
assert all(x['state'] in ['FAILED','SUCCEEDED','CANCELLED'] for x in st['children'])
proofs=json.loads((P/'terminal-batch-proofs.json').read_text());assert len(proofs)==4 and [x['proof']['status']['state'] for x in proofs]==['SUCCEEDED','SUCCEEDED','SUCCEEDED','FAILED']
counts=proofs[3]['proof']['status']['taskGroups']['group0']['counts'];assert int(counts['SUCCEEDED'])==17 and int(counts['FAILED'])==1
vms=json.loads((P/'terminal-runtime-pairs.json').read_text());assert len(vms)==55 and all(v['start'] and v['end'] for v in vms.values())
seconds=sum(max(v['end'])-min(v['start']) for v in vms.values());assert seconds>0;cost=seconds/3600*.15
empty={k:gc(*args,'--filter=name~fds-tree51-campa') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
for who,file in [('fds-worker','read-condition.json'),('fds-watchdog','controller-read-condition.json')]:
 gc('storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:'+who+'@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/file))
gc('projects','remove-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/fdsTree51TaskReader','--condition-from-file='+str(P/'task-read-condition.json'))
gc('projects','remove-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/fdsTree51WaveRunner','--condition-from-file='+str(P/'wave-run-condition.json'))
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());old=b['reservations'][WF];assert old['state']=='submitted';allowance=old['allowance_usd'];assert cost<allowance
 key='fds-tree51-campaign05';assert key not in b['reservations']
 old.update(state='spot_preemption_closed',cost=dict(usd=cost,allocation_seconds=seconds,rate_usd_per_hour=.15,stage='conservative_allocation_estimate'))
 b['estimated_spend_usd']+=cost;b['accounting']['spend_estimate_usd']=b['estimated_spend_usd'];b['reserved_usd']-=cost
 b['reservations'][key]=dict(state='reserved_before_upload',allowance_usd=allowance-cost,reserved_unix=time.time(),scope='Original campaign remainder only for unfinished cases and pending ancillary costs; corrected controller readiness required; no extra allowance')
 assert b['reservations']['fds-tree51-training']['allowance_usd']==20
 assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200
 B.write_text(json.dumps(b,indent=2)+'\n');save('closed.json',dict(passed=True,empty=empty,four_exact_grants_removed=True,allocation_seconds=seconds,compute_estimate_usd=cost,remainder_reserved_to=key,remaining_allowance_usd=allowance-cost,training_reserve_untouched=True))
print('campaign04 closed; original remainder reserved, no continuation submitted')
