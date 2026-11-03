"""Pin all failed-pilot objects and allocation evidence; never restarts anything."""
from cloud48_03 import *
import requests,base64,datetime
assert json.loads((P/'status.json').read_text())['controller']['state']=='FAILED'
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();s=requests.Session();s.headers['Authorization']='Bearer '+token
items=[];params={'prefix':PREFIX}
while True:
 q=s.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o',params=params,timeout=60);q.raise_for_status();d=q.json();items+=d.get('items',[])
 if not d.get('nextPageToken'):break
 params['pageToken']=d['nextPageToken']
out=P/'failed-pilot03';out.mkdir(exist_ok=True);files=[]
for v in items:
 rel=v['name'][len(PREFIX):];assert '..' not in Path(rel).parts
 q=s.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},timeout=120);q.raise_for_status();blob=q.content
 assert base64.b64encode(hashlib.md5(blob).digest()).decode()==v['md5Hash']
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob);files.append(dict(name=v['name'],generation=v['generation'],md5=v['md5Hash'],sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob)))
inv={k:gc(*args,'--filter=name~fds-tree48-pilot03') for k,args in {'vms':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};assert not any(inv.values());save('failure03-empty.json',inv)
logs=gc('logging','read','protoPayload.serviceName="compute.googleapis.com" AND "tree48-pilot03"','--freshness=3h','--limit=500');save('failure03-allocation-logs.json',logs)
save('failure03-archive.json',dict(passed=True,objects=files,empty=inv,controller_error=json.loads((P/'status.json').read_text())['controller'].get('error')))
print('Archived',len(files),'objects; resources empty; allocation log events',len(logs))
for e in logs:
 p=e.get('protoPayload',{});print(e.get('timestamp'),p.get('methodName'),p.get('resourceName'),e.get('operation',{}),p.get('status',{}))
