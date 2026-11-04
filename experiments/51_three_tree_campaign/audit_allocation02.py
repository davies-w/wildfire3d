"""Audit only campaign02 VM lifetimes and its failed Batch terminal snapshot."""
from cloud02 import *
import datetime,requests,base64
assert json.loads((P/'terminal-archive.json').read_text())['passed']
start=json.loads((P/'execution.json').read_text())['startTime']
logs=gc('logging','read','protoPayload.serviceName="compute.googleapis.com" AND "fds-tree51-campa" AND timestamp>="'+start+'"','--limit=5000');assert len(logs)<5000;save('terminal-allocation-logs.json',logs)
vms={}
for e in logs:
 p=e.get('protoPayload',{});m=p.get('methodName','');op=e.get('operation',{});name=p.get('resourceName','').split('/')[-1]
 if '.instances.' not in m or not name.startswith('fds-tree51-campa'):continue
 t=datetime.datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')).timestamp();v=vms.setdefault(name,{'start':[],'end':[]})
 if m.endswith('.insert') and op.get('first'):v['start'].append(t)
 if m.endswith('.delete') and op.get('last'):v['end'].append(t)
assert len(vms)==18 and all(v['start'] and v['end'] for v in vms.values());save('terminal-runtime-pairs.json',vms)
auth={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()};items=json.loads((P/'terminal-objects.json').read_text());v=max((x for x in items if x['name'].startswith(PREFIX+'wave-005/job-status.json.')),key=lambda x:float(x['name'].split('job-status.json.')[1]))
r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=60);r.raise_for_status();assert base64.b64encode(hashlib.md5(r.content).digest()).decode()==v['md5Hash'];j=r.json();assert j['status']['state']=='FAILED';counts=j['status']['taskGroups']['group0']['counts'];assert int(counts['SUCCEEDED'])==17 and int(counts['FAILED'])==1
save('terminal-batch-proofs.json',[dict(name=v['name'],generation=v['generation'],sha256=hashlib.sha256(r.content).hexdigest(),proof=j)]);print('18 allocation pairs and actual17SUCCEEDED/1FAILED terminal Batch verified')
