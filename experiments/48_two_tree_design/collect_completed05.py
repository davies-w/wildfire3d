"""Stream verified completed archives; retain only scientific solve files for publication."""
from cloud48_05 import *
import requests,base64,io,tarfile,csv,shutil
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
assert shutil.disk_usage(R).free>8*1024**3
receipt=json.loads((P/'terminal-archive.json').read_text());assert receipt['passed'];objects={x['name']:x for x in receipt['objects']}
completed=[x for x in json.loads((P/'terminal-completions.json').read_text()) if x['name'].endswith('/completion.json') and x['proof']['passed']];assert len(completed)==12
s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,allowed_methods=['GET'],status_forcelist=[429,500,502,503,504])))
s.headers['Authorization']='Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
out=R/'data/completed05';out.mkdir(exist_ok=True);proofs=[]
for record in completed:
 c=record['proof'];case=record['name'].split('/')[-2];dest=out/case;done=dest/'proof.json'
 if done.exists():proofs.append(json.loads(done.read_text()));continue
 dest.mkdir(exist_ok=True);prefix=record['name'].rsplit('/',1)[0]+'/';manifest=c['archive'];assert manifest['complete'];result=None;startup=None;files=[]
 class Parts(io.RawIOBase):
  def __init__(self):self.parts=iter(manifest['parts']);self.current=io.BytesIO()
  def readable(self):return True
  def readinto(self,buf):
   while True:
    n=self.current.readinto(buf)
    if n:return n
    try:p=next(self.parts)
    except StopIteration:return 0
    v=objects[prefix+p['name']];assert v['sha256']==p['sha256']
    r=s.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},timeout=120);r.raise_for_status();b=r.content;assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'];self.current=io.BytesIO(b)
 stream=io.BufferedReader(Parts())
 with tarfile.open(fileobj=stream,mode='r|gz') as t:
  for m in t:
   if not m.isfile():continue
   path=Path(m.name);assert '..' not in path.parts and not path.is_absolute()
   if m.name=='evidence/result.json':result=json.load(t.extractfile(m))
   if m.name=='evidence/startup.json':startup=json.load(t.extractfile(m))
   if path.parts[:2]!=('evidence','solve') or path.suffix not in {'.fds','.csv','.restart','.sf','.prt5','.smv','.xyz','.sz','.bnd'}:continue
   assert shutil.disk_usage(R).free>2*1024**3
   p=dest/Path(*path.parts[1:]);p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('wb') as f:shutil.copyfileobj(t.extractfile(m),f,1024*1024)
   files.append(dict(path=p.relative_to(dest).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
 while stream.read(1024*1024):pass
 assert result and result['passed'] and result['physical_time']>=180-1e-5 and startup and startup['passed']
 with (dest/'solve'/(case+'_devc.csv')).open() as f:
  rows=csv.reader(f);next(rows);keys=[x.strip().strip('"') for x in next(rows)];last=list(rows)[-1];assert float(last[keys.index('Time')])>=180-1e-5
 proof=dict(passed=True,case=case,physical_time_s=result['physical_time'],startup_passed=True,deck_sha256=c['deck_sha256'],archive_parts_verified=True,files=files);done.write_text(json.dumps(proof,indent=2));proofs.append(proof);print('Collected',case,flush=True)
(out/'proof.json').write_text(json.dumps(dict(passed=True,cases=proofs),indent=2));print('Collected all twelve completed bulk cases',flush=True)
