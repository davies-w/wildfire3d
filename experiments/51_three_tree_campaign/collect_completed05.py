"""Stream verified completed archives; retain only scientific solve files for publication."""
from cloud05 import *
import requests,base64,io,tarfile,csv,shutil,argparse,re,lzma,math
parser=argparse.ArgumentParser();parser.add_argument("--wave",required=True);args=parser.parse_args();wave=args.wave;assert re.fullmatch(r"wave-\d{6}",wave)
index=int(wave.split('-')[1]);entry=json.loads((R/'data/cloud05/inputs/items'/f'{index}.json').read_text());assert entry['id']==wave
bundle=R/'data/cloud05/inputs'/(wave+'.xz');assert sha(bundle)==entry['sha256'];payload=json.loads(lzma.decompress(bundle.read_bytes()));expected={x['pilot_case']:x for x in json.loads(payload['groups.json'])['wave']};assert len(expected)==entry['count']==1
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
assert shutil.disk_usage(R).free>8*1024**3
objects={x['name']:dict(name=x['name'],generation=x['generation'],bytes=int(x['size']),md5=x['md5Hash']) for x in json.loads((P/'objects.json').read_text())}
all_expected=dict(expected)
completed=[x for x in json.loads((P/'worker-proofs.json').read_text()) if x['name'].startswith(PREFIX+wave+'/') and x['name'].endswith('/completion.json') and x['proof']['passed']];assert len(completed)==len(expected) and {x['name'].split('/')[-2] for x in completed}==set(expected)
assert sum(x['proof']['archive']['bytes'] for x in completed)<2*10**9,'Bounded collection only; assess transfer allowance before larger wave'
s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,allowed_methods=['GET'],status_forcelist=[429,500,502,503,504])))
s.headers['Authorization']='Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
statuses=[x for x in objects.values() if x['name'].startswith(PREFIX+wave+'/job-status.json.')];v=max(statuses,key=lambda x:float(x['name'].split('job-status.json.')[1]));resp=s.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},timeout=60);resp.raise_for_status();assert base64.b64encode(hashlib.md5(resp.content).digest()).decode()==v['md5'];job=resp.json();counts=job['status']['taskGroups']['group0']['counts']
assert job['status']['state']=='SUCCEEDED' and int(counts['SUCCEEDED'])==1 and job['name'].endswith('/t51r05-c'+str(index))
save('collection-batch-'+wave+'.json',dict(passed=True,generation=v['generation'],sha256=hashlib.sha256(resp.content).hexdigest(),proof=job))
out=R/'data/completed05'/wave;out.mkdir(parents=True,exist_ok=True);proofs=[]
for record in completed:
 c=record['proof'];case=record['name'].split('/')[-2];assert c['deck_sha256']==expected[case]['deck_sha256'];dest=out/case;done=dest/'proof.json'
 if done.exists():proofs.append(json.loads(done.read_text()));continue
 dest.mkdir(exist_ok=True);prefix=record['name'].rsplit('/',1)[0]+'/';manifest=c['archive'];assert manifest['complete'];result=None;startup=next(x['proof'] for x in json.loads((P/'worker-proofs.json').read_text()) if x['name']==prefix+'startup.json');files=[]
 class Parts(io.RawIOBase):
  def __init__(self):self.parts=iter(manifest['parts']);self.current=io.BytesIO()
  def readable(self):return True
  def readinto(self,buf):
   while True:
    n=self.current.readinto(buf)
    if n:return n
    try:p=next(self.parts)
    except StopIteration:return 0
    v=objects[prefix+p['name']]
    r=s.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},timeout=120);r.raise_for_status();b=r.content;assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'] and base64.b64encode(hashlib.md5(b).digest()).decode()==v['md5'];self.current=io.BytesIO(b)
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
  rows=csv.reader(f);next(rows);keys=[x.strip().strip('"') for x in next(rows)];last=list(rows)[-1];assert all(math.isfinite(float(v)) for v in last) and float(last[keys.index('Time')])>=180-1e-5
 assert sha(dest/'solve'/(case+'.fds'))==expected[case]['deck_sha256']
 proof=dict(passed=True,case=case,physical_time_s=result['physical_time'],startup_passed=True,deck_sha256=c['deck_sha256'],archive_parts_verified=True,files=files);done.write_text(json.dumps(proof,indent=2));proofs.append(proof);print('Collected',case,flush=True)
(out/'proof.json').write_text(json.dumps(dict(passed=True,cases=proofs),indent=2));print('Collected currently completed continuations:',len(proofs),flush=True)
