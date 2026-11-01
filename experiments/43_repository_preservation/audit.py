"""Repository-wide preservation snapshot. Never executes simulations or training.

Original files remain unchanged. Financial records and credentials are excluded;
JSON metadata is exported with financial/credential fields removed. Archives are
inspected recursively; archives requiring redaction are represented by their
sanitized members. Content hashes and every disposition are recorded.
"""
from pathlib import Path
import os,sys,json,re,hashlib,subprocess,tarfile,zipfile,gzip,io,shutil,collections,ctypes
ROOT=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
D=R/'data/public';D.mkdir(parents=True,exist_ok=True)
PRIVATE=R/'results';PRIVATE.mkdir(exist_ok=True)
SECRET=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{25,}|AIza[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16}')
FINANCE=re.compile(r'budget|billing|invoice|estimated_spend|estimated_compute|cost|allowance|reservation|reserved_usd|price|pricing|\busd\b',re.I)
KEYS={'private_key','privatekey','client_secret','secret_access_key','aws_secret_access_key','access_token','refresh_token','password','api_key','authorization'}
SKIP_DIRS={'.git','.dvc','.venv','venv','node_modules','__pycache__','.pytest_cache','.mypy_cache','hf_dvc_mirror','project-model-archive','public-data-export'}
TEXT={'.py','.sh','.md','.html','.js','.css','.txt','.yaml','.yml','.toml','.cfg','.ini','.out','.log','.xml','.csv','.fds','.smv','.jsonl','.pem','.key'}
rows=[];exclusions=[];memo={};cache=ROOT/'.dvc/cache/files/md5';mirror=ROOT/'FDS/hf_dvc_mirror/files/md5'
tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
def redact(x):
 if isinstance(x,dict):return {k:redact(v) for k,v in x.items() if (k in {'stopped_by_budget','energy_budget','energy_budget_error'} or not FINANCE.search(k)) and k.lower() not in KEYS}
 if isinstance(x,list):return [redact(v) for v in x]
 if isinstance(x,str) and (re.search(r'\$\s*\d|\d\s*USD|estimated.{0,30}(?:cost|spend)|(?:cost|spend|allowance).{0,30}\d',x,re.I)):return '[financial details omitted]'
 return x

def cleanse(name,b):
 p=Path(name)
 if SECRET.search(b):return None,'credential excluded'
 if p.suffix.lower()=='.json':
  try:x=json.loads(b)
  except (ValueError,UnicodeDecodeError):return b,'byte-identical'
  y=redact(x)
  if x!=y:return (json.dumps(y,indent=2,ensure_ascii=False)+'\n').encode(),'financial/credential fields removed'
 return b,'byte-identical'

def hashes(f):
 st=f.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 if key in memo:return memo[key]
 md=hashlib.md5();sha=hashlib.sha256()
 with f.open('rb') as h:
  while b:=h.read(8*1024*1024):md.update(b);sha.update(b)
 assert f.stat().st_size==st.st_size and f.stat().st_mtime_ns==st.st_mtime_ns,f'Changed during audit: {f}'
 memo[key]=(md.hexdigest(),sha.hexdigest(),st.st_size);return memo[key]

def store(f,rel,mode='byte-identical',original=None):
 md,sha,size=hashes(f)
 dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():
  if dest.stat().st_ino!=f.stat().st_ino and hashes(dest)!=hashes(f):dest.unlink()
 if not dest.exists():
  libc=ctypes.CDLL(None,use_errno=True);clone=libc.clonefile
  clone.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];clone.restype=ctypes.c_int
  if clone(os.fsencode(f),os.fsencode(dest),0)!=0:raise OSError(ctypes.get_errno(),str(dest))
 for base in [cache,mirror]:
  obj=base/md[:2]/md[2:];obj.parent.mkdir(parents=True,exist_ok=True)
  if not obj.exists():os.link(dest,obj)
 rows.append(dict(path=rel,bytes=size,md5=md,sha256=sha,mode=mode,**({'source':original} if original else {})))

def process(f,rel):
 p=Path(rel);suffix=p.suffix.lower()
 if p.name in ['.DS_Store'] or suffix in ['.pyc','.pid'] or p.name.endswith('.lock') and p.name!='dvc.lock':
  exclusions.append(dict(path=rel,reason='transient process/cache file'));return
 if re.search(r'(^|/)(?:budget[^/]*|billing[^/]*|[^/]*invoice[^/]*|[^/]*runtime-reconciliation[^/]*|vm-runtime\.json|credentials[^/]*|\.env(?:\..*)?|id_rsa|id_ed25519)(/|$)',rel,re.I):
  exclusions.append(dict(path=rel,reason='spending ledger/financial record or credential file'));return
 if suffix in ['.tar','.tgz','.gz'] and tarfile.is_tarfile(f):
  changed=False
  with tarfile.open(f,'r:*') as tf:
   for m in tf:
    if not m.isfile():continue
    assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
    if re.search(r'(^|/)(budget[^/]*|credentials[^/]*|id_rsa|id_ed25519)(/|$)',m.name,re.I):changed=True;break
    if Path(m.name).suffix.lower() in TEXT|{'.json'}:
     b=tf.extractfile(m).read();clean,mode=cleanse(m.name,b)
     if clean!=b:changed=True;break
  if changed:
   # Repack only metadata; retain scientific member bytes without expanding
   # large solver arrays to disk. Runtime/physical budget flags are not ledgers.
   dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   temp=dest.with_name(dest.name+'.sanitizing')
   with tarfile.open(f,'r:*') as tf,tarfile.open(temp,'w:gz') as out:
    for m in tf:
     if not m.isfile():
      if m.isdir():out.addfile(m)
      continue
     if re.search(r'(^|/)(budget[^/]*|credentials[^/]*|id_rsa|id_ed25519)(/|$)',m.name,re.I):continue
     inp=tf.extractfile(m)
     if Path(m.name).suffix.lower() in TEXT|{'.json','.pem','.key'}:
      clean,mode=cleanse(m.name,inp.read())
      if clean is None:continue
      m.size=len(clean);out.addfile(m,io.BytesIO(clean))
     else:out.addfile(m,inp)
   os.replace(temp,dest);store(dest,rel,'archive metadata sanitized; scientific member bytes retained');return
 if suffix in TEXT|{'.json'}:
  b=f.read_bytes();clean,mode=cleanse(rel,b)
  if clean is None:exclusions.append(dict(path=rel,reason=mode));return
  if clean!=b:
   dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():dest.unlink()
   dest.write_bytes(clean);store(dest,rel,mode);return
 elif suffix in ['.pt','.pth','.npz','.pkl','.pickle','.joblib','.safetensors']:
  if zipfile.is_zipfile(f):
   with zipfile.ZipFile(f) as z:
    for name in z.namelist():
     if name.endswith(('.pkl','.json','.txt')):
      assert not SECRET.search(z.read(name)),f'Credential in model archive: {rel}'
  elif suffix in ['.pkl','.pickle','.joblib']:assert not SECRET.search(f.read_bytes()),rel
 store(f,rel)

paths=[]
for base,dirs,files in os.walk(ROOT):
 relbase=Path(base).relative_to(ROOT)
 dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not (relbase==Path('.') and d in ['FDS']) and not (relbase==Path('experiments') and d==R.name)]
 for name in files:
  f=Path(base)/name
  if f.is_symlink():
   if not f.exists():exclusions.append(dict(path=str(f.relative_to(ROOT)),reason='dangling symlink'));continue
  if f.is_file():paths.append(f)
for i,f in enumerate(sorted(paths)):
 process(f,str(f.relative_to(ROOT)))
 if i%2000==0:print(json.dumps(dict(scanned=i,total=len(paths),exported=len(rows))),flush=True)
# Include engine-area source files explicitly tracked by Git, not the installed engine.
for name in sorted(tracked):
 if name.startswith('FDS/') and (ROOT/name).is_file():process(ROOT/name,name)
manifest=dict(scope='All locally present repository files, including ignored scientific artifacts, except installed engine/dependencies/caches and duplicate prior exports. Tracked engine-area source is included. No training or simulation was run.',files=rows,excluded=exclusions,source_files=len(paths),exported_files=len(rows),logical_bytes=sum(x['bytes'] for x in rows),unique_objects=len({x['md5'] for x in rows}))
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(PRIVATE/'snapshot-complete.json').write_text(json.dumps({k:v for k,v in manifest.items() if k not in ['files','excluded']},indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in ['files','excluded']}),flush=True)
