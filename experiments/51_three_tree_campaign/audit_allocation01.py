"""Terminal allocation audit and immutable capture of saved successful Batch state."""
from cloud import *
import datetime,requests,base64
assert json.loads((P/'terminal-archive.json').read_text())['passed']
logs=gc('logging','read','protoPayload.serviceName="compute.googleapis.com" AND "fds-tree51-campa"','--freshness=12h','--limit=5000');assert len(logs)<5000;save('terminal-allocation-logs.json',logs)
vms={}
for e in logs:
 p=e.get('protoPayload',{});m=p.get('methodName','');op=e.get('operation',{});name=p.get('resourceName','').split('/')[-1]
 if '.instances.' not in m or not name.startswith('fds-tree51-campa'):continue
 t=datetime.datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')).timestamp();v=vms.setdefault(name,{'start':[],'end':[]})
 if m.endswith('.insert') and op.get('first'):v['start'].append(t)
 if m.endswith('.delete') and op.get('last'):v['end'].append(t)
assert len(vms)==78 and all(v['start'] and v['end'] for v in vms.values());save('terminal-runtime-pairs.json',vms)
auth={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()};items=json.loads((P/'terminal-objects.json').read_text());proofs=[]
for group,count in [(f'wave-{i:03d}',6 if i==0 else 18) for i in range(5)]:
 v=max((x for x in items if x['name'].startswith(PREFIX+group+'/job-status.json.')),key=lambda x:float(x['name'].split('job-status.json.')[1]))
 r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=60);r.raise_for_status();assert base64.b64encode(hashlib.md5(r.content).digest()).decode()==v['md5Hash'];j=r.json()
 if j['status']['state']!='SUCCEEDED':
  assert group=='wave-004','Only final wave may finish after controller failure'
  job=json.loads((P/'terminal-existing-jobs.json').read_text())[0];assert job['name'].endswith('/fds-tree51-campaign01-wave-004') and job['status']['state']=='SUCCEEDED'
  receipt=P/'terminal-final-job-upload.json';path=P/'terminal-existing-jobs.json';name=PREFIX+'terminal-audit/final-job-observed-before-delete.json'
  if not receipt.exists():
   gc('storage','cp',str(path),'gs://'+BUCKET+'/'+name,'--if-generation-match=0');save(receipt.name,gc('storage','objects','describe','gs://'+BUCKET+'/'+name))
  meta=json.loads(receipt.read_text());v=dict(name=name,generation=meta['generation'],md5Hash=meta['md5_hash'])
  r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(name,safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=60);r.raise_for_status();assert r.content==path.read_bytes() and base64.b64encode(hashlib.md5(r.content).digest()).decode()==v['md5Hash'];j=r.json()[0]
 assert j['status']['state']=='SUCCEEDED';assert int(j['status']['taskGroups']['group0']['counts']['SUCCEEDED'])==count
 proofs.append(dict(name=v['name'],generation=v['generation'],sha256=hashlib.sha256(r.content).hexdigest(),proof=j))
save('terminal-batch-proofs.json',proofs);print('All78 allocation pairs and five successful Batch waves verified')
