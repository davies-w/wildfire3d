from cloud48_04 import *
import datetime
assert not (P/'failure04-closed.json').exists()
assert json.loads((R/'data/canaries04/proof.json').read_text())['passed']
a=json.loads((P/'failure04-archive.json').read_text());assert a['passed'] and not any(a['empty'].values())
logs=json.loads((P/'failure04-allocation-logs.json').read_text());vms={}
for e in logs:
 p=e.get('protoPayload',{});m=p.get('methodName','');op=e.get('operation',{});name=p.get('resourceName','').split('/')[-1]
 if '.instances.' not in m:continue
 t=datetime.datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')).timestamp();v=vms.setdefault(name,{'start':[],'end':[]})
 if m.endswith('.insert') and op.get('first'):v['start'].append(t)
 if m.endswith('.delete') and op.get('last'):v['end'].append(t)
assert len(vms)==4 and all(v['start'] and v['end'] for v in vms.values())
seconds=sum(max(v['end'])-min(v['start']) for v in vms.values());cost=seconds/3600*.15
assert not gc('compute','instances','list','--filter=name~fds-tree48-pilot04')
assert not gc('compute','disks','list','--filter=name~fds-tree48-pilot04')
assert not gc('batch','jobs','list','--location=us-central1','--filter=name~fds-tree48-pilot04')
gc('storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'read-condition.json'))
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());old=b['reservations'][WF];assert old['state']=='submitted';allowance=old['allowance_usd'];old.update(state='controller_failure_closed',cost={'stage':'conservative_allocation_runtime_estimate','usd':cost,'seconds':seconds,'rate_usd_per_hour':.15},terminal_evidence=str(P/'failure04-closed.json'))
 b['estimated_spend_usd']+=cost;b['accounting']['spend_estimate_usd']=b['estimated_spend_usd'];b['reserved_usd']-=cost
 b['reservations']['fds-tree48-pilot05']=dict(state='reserved_from_failed_pilot04',allowance_usd=allowance-cost,reserved_unix=time.time(),scope='Remainder of original pilot allowance; includes pending image-build and shared costs, no extra allowance')
 B.write_text(json.dumps(b,indent=2)+'\n')
save('failure04-closed.json',dict(passed=True,resources_empty=True,grant_removed=True,allocation_seconds=seconds,compute_estimate_usd=cost,build_and_shared_costs_still_reserved_under_pilot05=True))
print('Closed original pilot; remaining allowance transferred without increasing total commitment.')
