"""Preserve the terminal stop test, including its uploaded restart, without rerunning it."""
from cloud48_05 import *
import requests,base64,concurrent.futures
Q=R/'private-stopcheck01';items=json.loads((Q/'objects.json').read_text());auth={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()}
def fetch(v):
 p=Q/'archive'/v['name'].removeprefix('tree48/stopcheck01/');p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():b=p.read_bytes()
 else:
  r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=180);r.raise_for_status();b=r.content
 assert len(b)==int(v['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==v['md5Hash'];p.write_bytes(b)
 return dict(name=v['name'],generation=v['generation'],md5=v['md5Hash'],sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,items))
empty={k:gc(*args) for k,args in {'jobs':('batch','jobs','list','--location=us-central1','--filter=name~fds-tree48-stopcheck01'),'vms':('compute','instances','list','--filter=name~fds-tree48-stopcheck01'),'disks':('compute','disks','list','--filter=name~fds-tree48-stopcheck01')}.items()}
(Q/'archive-proof.json').write_text(json.dumps(dict(passed=True,objects=records,empty=empty),indent=2));print('Archived',len(records),'objects; empty:',not any(empty.values()))
