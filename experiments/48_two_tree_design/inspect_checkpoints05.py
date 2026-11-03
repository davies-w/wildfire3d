"""Read six unfinished non-fine checkpoint archives without a disk mirror or solver."""
from cloud48_05 import *
import requests,base64,io,tarfile,csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
items={x['name']:x for x in json.loads((P/'terminal-objects.json').read_text())}
cases=['000181_baseline','000997_baseline','001186_baseline','001991_baseline','000830_expanded','001824_expanded']
s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,allowed_methods=['GET'],status_forcelist=[429,500,502,503,504])))
s.headers['Authorization']='Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
def fetch(name,expected=None):
 v=items[name];r=s.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(name,safe=''),params={'alt':'media','generation':v['generation']},timeout=120);r.raise_for_status();b=r.content
 assert len(b)==int(v['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==v['md5Hash']
 if expected:assert hashlib.sha256(b).hexdigest()==expected
 return b
for short in cases:
 case='tree48_'+short;out=P/'checkpoint-inspection'/case;out.mkdir(parents=True,exist_ok=True)
 if (out/'proof.json').exists():continue
 candidates=sorted(n for n in items if '/'+case+'/checkpoints/' in n and n.endswith('/archive-manifest.json'))
 assert candidates,case
 name=candidates[-1];manifest=json.loads(fetch(name));assert manifest['complete'];prefix=name.rsplit('/',1)[0]+'/'
 class Parts(io.RawIOBase):
  def __init__(self):self.parts=iter(manifest['parts']);self.current=io.BytesIO()
  def readable(self):return True
  def readinto(self,buf):
   while True:
    n=self.current.readinto(buf)
    if n:return n
    try:p=next(self.parts)
    except StopIteration:return 0
    self.current=io.BytesIO(fetch(prefix+p['name'],p['sha256']))
 stream=io.BufferedReader(Parts());saved=[]
 with tarfile.open(fileobj=stream,mode='r|gz') as t:
  for m in t:
   if m.isfile() and m.size<20_000_000 and m.name.endswith(('.csv','.out','.log','checkpoint.json')):
    p=out/Path(m.name).name;p.write_bytes(t.extractfile(m).read());saved.append(dict(name=p.name,sha256=sha(p)))
 # Exhaust the stream so every archive part is verified even after tar EOF.
 while stream.read(1024*1024):pass
 with (out/(case+'_devc.csv')).open() as f:
  reader=csv.reader(f);next(reader);keys=[x.strip().strip('"') for x in next(reader)];rows=list(reader);physical=float(rows[-1][keys.index('Time')])
 proof=dict(case=case,manifest=name,generation=items[name]['generation'],physical_time_last_device_s=physical,files=saved,all_parts_hash_verified=True)
 (out/'proof.json').write_text(json.dumps(proof,indent=2));print(case,physical,flush=True)
