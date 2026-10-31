"""Export project-wide model/data artifacts without financial records or credentials."""
from pathlib import Path
import re,json,hashlib,zipfile,os
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'experiments/38_history8_shared64/data/project-model-archive';D.mkdir(exist_ok=True)
secret=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|hf_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16}|"private_key"\s*:')
finance=re.compile(r'budget|cost|spend|reserv|allowance|billing|invoice|usd|price|\$\s*\d',re.I)
ext={'.pt','.pth','.safetensors','.pkl','.pickle','.joblib','.npz','.npy','.json','.csv'}
files=[];omitted=[];counts={}
def scrub(x):
 if isinstance(x,dict):return {k:scrub(v) for k,v in x.items() if not finance.search(k)}
 if isinstance(x,list):return [scrub(v) for v in x]
 if isinstance(x,str) and finance.search(x):return '[financial commentary omitted]'
 return x
for f in sorted((ROOT/'experiments').rglob('*')):
 if not f.is_file() or f.suffix not in ext:continue
 rel=f.relative_to(ROOT/'experiments')
 if any('provenance' in x or x in ['project-model-archive','public-data-export','jobs','__pycache__'] for x in rel.parts):continue
 if finance.search(f.name):omitted.append(str(rel));continue
 if not ('data' in rel.parts or 'results' in rel.parts or f.suffix in {'.pt','.pth','.safetensors','.pkl','.pickle','.joblib','.npz','.npy'} or any(k in f.name for k in ['schema','split','groups','cases','design','training','development','coverage'])):continue
 b=f.read_bytes()
 if f.suffix not in {'.npz','.npy','.pt','.pth'} and secret.search(b):raise RuntimeError('Credential pattern found: '+str(rel))
 if f.suffix=='.npy':
  # Numeric tensor payloads contain no serialized credential strings. Object/string arrays are scanned.
  header=b[:4096]
  if re.search(rb"['\"]descr['\"]\s*:\s*['\"][^'\"]*[OUS]",header):assert not secret.search(b),rel
 if zipfile.is_zipfile(f):
  with zipfile.ZipFile(f) as z:
   for n in z.namelist():
    if n.endswith(('.pkl','.json','.txt')):assert not secret.search(z.read(n)),str(rel)+'::'+n
    elif n.endswith('.npy'):
     with z.open(n) as member:head=member.read(4096)
     if re.search(rb"['\"]descr['\"]\s*:\s*['\"][^'\"]*[OUS]",head):assert not secret.search(z.read(n)),str(rel)+'::'+n
 mode='byte-identical'
 if f.suffix=='.json':
  try:obj=json.loads(b)
  except (ValueError,UnicodeDecodeError):omitted.append(str(rel));continue
  clean=scrub(obj)
  if obj!=clean:b=(json.dumps(clean,indent=2)+'\n').encode();mode='financial metadata removed'
 elif f.suffix=='.csv' and finance.search(b.decode('utf-8',errors='replace')):omitted.append(str(rel));continue
 out=D/rel;out.parent.mkdir(parents=True,exist_ok=True)
 if not out.exists():
  if mode=='byte-identical':os.link(f,out)
  else:out.write_bytes(b)
 else:assert out.read_bytes()==b,out
 files.append({'path':str(rel),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mode':mode});counts[rel.parts[0]]=counts.get(rel.parts[0],0)+1
 if len(files)%2000==0:print('Scanned',len(files),flush=True)
(D/'manifest.json').write_text(json.dumps({'policy':'All locally present model/checkpoint and numerical training/evaluation files across experiments, including nested attempts. Scientific JSON and split/schema records included; financial fields/commentary removed. Budget files, provenance bundles, cloud jobs, tar packages and credentials excluded. Binary models and arrays byte-identical. Original local evidence retained. No raw FDS fields are needed for loading the exported numerical datasets.','files':files,'excluded_paths':omitted,'experiments':counts},indent=2))
print(json.dumps({'files':len(files),'bytes':sum(x['bytes'] for x in files),'experiments':counts}),flush=True)
