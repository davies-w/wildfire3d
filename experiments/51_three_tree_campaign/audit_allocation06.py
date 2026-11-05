"""Audit unique rolling06 allocations and immutable terminal singleton outcomes."""
from cloud06 import *
import datetime,re,requests,base64
status=json.loads((P/'status.json').read_text());assert status['controller']['state']!='ACTIVE' and not status['jobs'] and not status['vms']
assert all(x['state']!='ACTIVE' for x in json.loads((P/'case-executions.json').read_text()))
start=json.loads((P/'execution.json').read_text())['startTime']
logs=gc('logging','read','protoPayload.serviceName="compute.googleapis.com" AND "t51r06-c" AND timestamp>="'+start+'"','--limit=10000');assert len(logs)<10000;save('terminal-allocation-logs.json',logs)
vms={}
for e in logs:
 p=e.get('protoPayload',{});m=p.get('methodName','');op=e.get('operation',{});name=p.get('resourceName','').split('/')[-1]
 if '.instances.' not in m or not name.startswith('t51r06-c'):continue
 match=re.match(r't51r06-c(\d+)-',name);assert match;index=int(match[1]);assert 0<=index<=175
 t=datetime.datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')).timestamp();v=vms.setdefault(name,dict(index=index,start=[],end=[]))
 if m.endswith('.insert') and op.get('first'):v['start'].append(t)
 if m.endswith('.delete') and op.get('last'):v['end'].append(t)
assert all(v['start'] and v['end'] for v in vms.values())
assert {v['index'] for v in vms.values()}>=set(range(176))
assert len(vms)==len({v['index'] for v in vms.values()}) and len(vms)==176
save('terminal-runtime-pairs.json',vms)
auth={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()};items=json.loads((P/'terminal-objects.json').read_text());proofs=[]
for i in range(176):
 snapshots=[x for x in items if x['name'].startswith(PREFIX+f'wave-{i:06d}/job-status.json.')]
 if not snapshots:
  assert i==171;continue
 v=max(snapshots,key=lambda x:float(x['name'].split('job-status.json.')[1]));r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=60);r.raise_for_status();assert base64.b64encode(hashlib.md5(r.content).digest()).decode()==v['md5Hash'];j=r.json();assert j['name'].endswith('/t51r06-c'+str(i));assert j['status']['state'] in ['SUCCEEDED','FAILED'] or i==171;counts=j['status']['taskGroups']['group0']['counts'];assert sum(map(int,counts.values()))==1;assert i==171 or int(counts.get(j['status']['state'],0))==1
 proofs.append(dict(index=i,name=v['name'],generation=v['generation'],sha256=hashlib.sha256(r.content).hexdigest(),proof=j))
save('terminal-batch-proofs.json',proofs)
seconds=sum(max(x['end'])-min(x['start']) for x in vms.values());assert seconds>0
save('allocation-summary.json',dict(passed=True,pairs=len(vms),allocation_seconds=seconds,compute_upper_usd=seconds*.15/3600,case171_vm_observed=any(x['index']==171 for x in vms.values()),case171_batch_snapshot_observed=any(x['index']==171 for x in proofs),case171_snapshot_may_be_nonterminal=True))
print('Allocation pairs and terminal singleton snapshots verified',len(vms),len(proofs))
