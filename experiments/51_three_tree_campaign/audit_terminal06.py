"""Stream-verify immutable private GCS objects without a bulk local mirror."""
from cloud06 import *
import requests,base64,concurrent.futures,threading
status=json.loads((P/'status.json').read_text());assert status['controller']['state']!='ACTIVE' and not status['jobs'] and not status['vms']
children=json.loads((P/'case-executions.json').read_text());assert all(x['state']!='ACTIVE' for x in children)
items=json.loads((P/'terminal-objects.json').read_text());assert items and all(x['name'].startswith(PREFIX) for x in items) and sum(int(x['size']) for x in items)<30*10**9;receipts=P/'terminal-object-hashes';receipts.mkdir(exist_ok=True)
token_lock=threading.Lock();token_value=None;token_time=0
def auth_headers():
 global token_value,token_time
 with token_lock:
  if token_value is None or time.monotonic()-token_time>2400:
   token_value=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();token_time=time.monotonic()
  return {'Authorization':'Bearer '+token_value}
sessions=threading.local()
def verify(v):
 if not hasattr(sessions,"http"):sessions.http=requests.Session()
 dest=receipts/(hashlib.sha256(v['name'].encode()).hexdigest()+'.json')
 if dest.exists():
  old=json.loads(dest.read_text())
  assert old['generation']==v['generation'] and old['md5']==v['md5Hash'];return old
 for attempt in range(4):
  try:
   auth=auth_headers()
   md5=hashlib.md5();sha256=hashlib.sha256();size=0
   with sessions.http.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=(30,120),stream=True) as r:
    r.raise_for_status()
    for chunk in r.iter_content(1024*1024):md5.update(chunk);sha256.update(chunk);size+=len(chunk)
   assert size==int(v['size']) and base64.b64encode(md5.digest()).decode()==v['md5Hash']
   result=dict(name=v['name'],generation=v['generation'],md5=v['md5Hash'],sha256=sha256.hexdigest(),bytes=size,preserved_at='gs://'+BUCKET+'/'+v['name']);tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(result));tmp.replace(dest);return result
  except requests.RequestException:
   if attempt==3:raise
   time.sleep(2**attempt)
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 records=[]
 for result in pool.map(verify,items):
  records.append(result)
  if len(records)%50==0:print('Verified',len(records),'/',len(items),flush=True)
empty={k:gc(*args,'--filter=name~t51r06') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
save('terminal-archive.json',dict(passed=True,objects=records,empty=empty,storage='Original immutable private GCS generations; streamed MD5/SHA verification, no local bulk mirror'))
print('Verified all objects and empty resources',flush=True)
