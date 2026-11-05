"""Remove only terminal campaign06's four grants; no ledger transfer or deployment."""
from cloud06 import *
assert WF=='t51r06' and P.name=='private06'
assert not (P/'grants-retired.json').exists(),'Already retired; do not repeat'
a=json.loads((P/'terminal-archive.json').read_text());assert a['passed'] and len(a['objects'])==len(json.loads((P/'terminal-objects.json').read_text())) and not any(a['empty'].values())
s=json.loads((P/'status.json').read_text());assert s['controller']['state']=='SUCCEEDED' and json.loads(s['controller']['result'])['requires_allocation_and_scientific_audit']
assert all(x['state'] in ['FAILED','SUCCEEDED','CANCELLED'] for x in json.loads((P/'case-executions.json').read_text()))
vms=json.loads((P/'terminal-runtime-pairs.json').read_text());assert len(vms)==176 and all(v['start'] and v['end'] for v in vms.values())
proofs=json.loads((P/'terminal-batch-proofs.json').read_text());assert len(proofs)>=175 and json.loads((P/'allocation-summary.json').read_text())['passed']
empty={k:gc(*args,'--filter=name~t51r06') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
expected={'read-condition.json':'tree51-campaign06-read','controller-read-condition.json':'tree51-campaign06-controller-read','task-read-condition.json':'tree51-task-read06','execution-run-condition.json':'tree51-campaign06-execution-run'}
for file,title in expected.items():assert json.loads((P/file).read_text())['title']==title
for who,file in [('fds-worker','read-condition.json'),('fds-watchdog','controller-read-condition.json')]:
 gc('storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:'+who+'@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/file))
for role,file in [('fdsTree51TaskReader','task-read-condition.json'),('fdsTree51WaveRunner','execution-run-condition.json')]:
 gc('projects','remove-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/'+role,'--condition-from-file='+str(P/file))
policies={'bucket':gc('storage','buckets','get-iam-policy','gs://'+BUCKET),'project':gc('projects','get-iam-policy',PROJECT)}
for policy in policies.values():
 assert not any(b.get('condition',{}).get('title') in set(expected.values()) for b in policy.get('bindings',[]))
save('grants-retired.json',dict(passed=True,exact_titles=list(expected.values()),four_exact_grants_removed=True,independent_policy_readback_verified=True,empty=empty,ledger_unchanged=True))
print('Four exact campaign06 grants retired; ledger unchanged; no continuation submitted')
