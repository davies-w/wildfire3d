"""Pin failed-case final archives; inspect solver evidence without restarting jobs."""
from cloud48_05 import *
import requests,base64,concurrent.futures,tarfile,io
items={x['name']:x for x in json.loads((P/'objects.json').read_text())}
proofs=json.loads((P/'worker-proofs.json').read_text());token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
def fetch(name):
 v=items[name];path=P/'failed-cases'/name[len(PREFIX):];path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():b=path.read_bytes()
 else:
  r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(name,safe=''),params={'alt':'media','generation':v['generation']},headers={'Authorization':'Bearer '+token},timeout=180);r.raise_for_status();b=r.content
 assert base64.b64encode(hashlib.md5(b).digest()).decode()==v['md5Hash'];path.write_bytes(b)
 return dict(name=name,generation=v['generation'],md5=v['md5Hash'],sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
results=[]
for x in proofs:
 if not x['name'].endswith('/completion.json') or x['proof']['passed']:continue
 prefix=x['name'].rsplit('/',1)[0]+'/';manifest=x['proof']['archive'];names=[prefix+v['name'] for v in manifest['parts']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,names))
 for v,r in zip(manifest['parts'],records):assert v['sha256']==r['sha256']
 # Stream consecutive verified chunks instead of copying multi-GB archives.
 class Parts(io.RawIOBase):
  def __init__(self):self.paths=iter(names);self.current=None
  def readable(self):return True
  def readinto(self,buf):
   while True:
    if self.current is None:
     try:self.current=(P/'failed-cases'/next(self.paths)[len(PREFIX):]).open('rb')
     except StopIteration:return 0
    n=self.current.readinto(buf)
    if n:return n
    self.current.close();self.current=None
 evidence={}
 with tarfile.open(fileobj=io.BufferedReader(Parts()),mode='r|gz') as t:
  for m in t:
   if m.isfile() and (m.name.endswith(('failure.txt','result.json','.out','.log'))) and m.size<20_000_000:
    evidence[m.name]=t.extractfile(m).read().decode(errors='replace')
 result=dict(case=prefix,objects=records,evidence=evidence);results.append(result)
 save('failed-case-diagnosis.json',results)
 print(prefix,flush=True)
 for n,v in evidence.items():
  if n.endswith(('failure.txt','result.json')):print(n,v[-5000:],flush=True)
  elif '/solve/' in n:print(n,v[-2500:],flush=True)
