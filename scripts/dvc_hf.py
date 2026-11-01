"""Cache-free DVC metadata and scoped Hugging Face uploads. Never uploads a whole directory blindly."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time,tarfile,zipfile,io
import yaml,requests
from huggingface_hub import HfApi
import hf_xet
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'experiments/43_repository_preservation/results/direct-hf';STATE.mkdir(parents=True,exist_ok=True)
SECRET=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{25,}|AIza[A-Za-z0-9_-]{30,}|(?:AKIA|ASIA)[A-Z0-9]{16}')
FIN=re.compile(r'budget|billing|invoice|estimated_spend|estimated_compute|cost|allowance|reservation|reserved_usd|price|pricing|\busd\b',re.I)
KEYS={'private_key','client_secret','secret_access_key','aws_secret_access_key','access_token','refresh_token','password','api_key','authorization'}
PUBLIC_EXCEPTIONS={'stopped_by_budget','energy_budget','energy_budget_error'}
_hashes={};review={};objects={}
reviewed_path=ROOT/'scripts/dvc_hf_reviewed.json'
reviewed=json.loads(reviewed_path.read_text()) if reviewed_path.exists() else {}
def digest(p):
 s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 if key not in _hashes:
  m=hashlib.md5();h=hashlib.sha256()
  with p.open('rb') as f:
   while b:=f.read(8*1024*1024):m.update(b);h.update(b)
  assert (p.stat().st_size,p.stat().st_mtime_ns)==(s.st_size,s.st_mtime_ns),str(p)
  _hashes[key]=(m.hexdigest(),h.hexdigest())
 return _hashes[key]
def blocked_data(x):
 if isinstance(x,dict):
  for k,v in x.items():
   k=str(k)
   if k.lower() in KEYS and v:return 'credential field'
   reference=isinstance(v,str) and bool(re.fullmatch(r'[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}',v)) and Path(k).suffix in {'.py','.json','.pt','.npz','.yaml','.yml','.fds'}
   if FIN.search(k) and k not in PUBLIC_EXCEPTIONS and not reference:return 'financial metadata field'
   reason=blocked_data(v)
   if reason:return reason
 elif isinstance(x,list):
  for v in x:
   reason=blocked_data(v)
   if reason:return reason
 elif isinstance(x,str) and re.search(r'\$\s*\d|\d\s*USD|estimated.{0,30}(?:cost|spend)|(?:cost|spend|allowance).{0,30}\d',x,re.I):return 'financial detail'
 return None
def byte_policy(name,b):
 if SECRET.search(b):return 'credential signature'
 suffix=Path(name).suffix.lower()
 if suffix=='.json':
  try:return blocked_data(json.loads(b))
  except (ValueError,UnicodeDecodeError):pass
 if suffix in {'.txt','.log','.csv','.out','.html','.md','.yaml','.yml','.ini','.cfg'} and re.search(rb'\$\s*\d|\d\s*USD',b,re.I):return 'financial text'
 return None
def path_policy(name):
 parts=Path(name).parts
 if any(x in parts for x in ['.git','.venv','__pycache__','.artifact-staging','.dvc']):return 'runtime/tool internals'
 if name.startswith('experiments/43_repository_preservation/data/private/') or '/results/file-tracking-audit/' in name or '/results/direct-hf/' in name:return 'private audit/recovery records'
 p=Path(name)
 if p.suffix.lower() in {'.p12','.pfx','.key','.pem'}:return 'key or certificate container'
 if p.name in {'.DS_Store'} or p.suffix in {'.pyc','.pid','.lock'}:return 'transient file'
 if p.name in {'.dvcignore','dvc.lock','dvc.yaml'}:return 'tracking metadata (Git)'
 if any(x.startswith('.env') or x in {'id_rsa','id_ed25519'} for x in parts):return 'credential path'
 if p.suffix.lower() in {'.json','.csv','.txt','.html','.log','.yaml','.yml'} and FIN.search(p.name) and 'energy_budget' not in p.name:return 'financial record path'
 if any(x.startswith('billing-audit') for x in parts):return 'financial record path'
 return None
prior_path=ROOT/'experiments/43_repository_preservation/data/private/storage-cleanup/public-manifest.json'
prior={x.get('source',x['path']):x for x in json.loads(prior_path.read_text())['files']} if prior_path.exists() else {}
def approve(p):
 name=str(p.relative_to(ROOT));st=p.lstat();key=(name,st.st_size,st.st_mtime_ns,st.st_ino)
 if key in review:return review[key]
 reason=path_policy(name)
 if not reason and p.is_symlink():reason='symlink requires separate review'
 if not reason:
  md,sha=digest(p);old=prior.get(name)
  if old and old['sha256']==sha and old['mode']=='byte-identical':review[key]=None;return None
  if old and 'sanitized' in old['mode']:reason='original archive contains excluded metadata'
  elif old and 'removed' in old['mode']:reason='original metadata requires redaction'
  else:
   if p.suffix.lower() in {'.gz','.tar','.tgz'} and tarfile.is_tarfile(p):
    with tarfile.open(p,'r:*') as tf:
     for member in tf:
      if member.isfile():
       reason=path_policy(member.name) or byte_policy(member.name,tf.extractfile(member).read())
       if reason:reason='archive member: '+reason;break
   else:
    # Binary numerical/model data and text are scanned for literal credentials.
    reason=byte_policy(name,p.read_bytes())
 if reason=='financial text' and name in reviewed and digest(p)[1]==reviewed[name]['sha256']:reason=None
 review[key]=reason;return reason
def register(p):
 reason=approve(p)
 if reason:raise ValueError(str(p.relative_to(ROOT))+': '+reason)
 md,sha=digest(p);objects[md]={'source':str(p.relative_to(ROOT)),'size':p.stat().st_size,'sha256':sha};return md

def directory(entries):
 b=json.dumps(sorted(entries,key=lambda x:x['relpath']),sort_keys=True).encode();md=hashlib.md5(b).hexdigest()+'.dir';p=STATE/'metadata'/md;p.parent.mkdir(exist_ok=True);p.write_bytes(b);objects[md]={'source':str(p.relative_to(ROOT)),'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'directory':True};return md

def upload(plan_path):
 plan=json.loads(plan_path.read_text());items=list(plan['objects'].items());api=HfApi();verified=0;uploaded=0
 for h,x in items:
  p=(ROOT/x['source']).resolve();assert p.is_relative_to(ROOT),x['source']
  assert re.fullmatch(r'[0-9a-f]{32}(?:\.dir)?',h),h
  if x.get('directory'):
   assert p.is_relative_to(STATE/'metadata') and h.endswith('.dir')
   for entry in json.loads(p.read_bytes()):
    assert set(entry)=={'md5','relpath'} and not Path(entry['relpath']).is_absolute() and '..' not in Path(entry['relpath']).parts
    assert entry['md5'] in plan['objects'],'Directory has an unreviewed object'

 for start in range(0,len(items),100):
  batch=items[start:start+100];paths=['wildfire3d/files/md5/'+h[:2]+'/'+h[2:] for h,x in batch]
  remote={x.path:x for x in api.get_bucket_paths_info('wdavies/dvc_storage',paths,token=False)};hashed=hf_xet.hash_files([str(ROOT/x['source']) for h,x in batch]);adds=[];expected=[]
  for (h,x),dest,xh in zip(batch,paths,hashed):
   p=ROOT/x['source'];md,sha=digest(p);assert md==h.removesuffix('.dir') and sha==x['sha256']
   if not x.get('directory'):assert approve(p) is None
   expected.append((dest,xh.file_size,xh.hash))
   found=remote.get(dest)
   if not found or (found.size,found.xet_hash)!=(xh.file_size,xh.hash):adds.append((p,dest))
  if adds:api.batch_bucket_files('wdavies/dvc_storage',add=adds);uploaded+=len(adds)
  remote={x.path:x for x in api.get_bucket_paths_info('wdavies/dvc_storage',paths,token=False)}
  for dest,size,xhash in expected:assert (remote[dest].size,remote[dest].xet_hash)==(size,xhash),dest
  for h,x in batch:assert digest(ROOT/x['source'])==(h.removesuffix('.dir'),x['sha256']),'Source changed during upload'
  verified+=len(batch)
  if start%1000==0:print('Verified',verified,'/',len(items),'uploaded',uploaded,flush=True)
  time.sleep(.15)
 # Anonymous content readback of every newly generated directory record.
 for h,x in items:
  if x.get('directory'):
   r=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:],timeout=90);r.raise_for_status();assert hashlib.md5(r.content).hexdigest()==h[:-4]
 proof=dict(passed=True,objects=verified,uploaded_objects=uploaded,remote_size_and_xet_verified=True,directory_anonymous_readback=True,cache_used=False,mirror_used=False,plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())
 (STATE/'upload-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)

def definitions():
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'); result=[]
 for name in tracked:
  if Path(name).name!='dvc.yaml':continue
  p=ROOT/name;doc=yaml.safe_load(p.read_text()) or {};lp=p.with_name('dvc.lock');lock=yaml.safe_load(lp.read_text()) if lp.exists() else {'schema':'2.0','stages':{}}
  for sn,stage in doc.get('stages',{}).items():
   if 'foreach' in stage:continue
   base=p.parent/stage.get('wdir','.')
   for kind in ['outs','metrics','plots']:
    for value in stage.get(kind,[]):
     path=value if isinstance(value,str) else next(iter(value));target=Path(os.path.abspath(base/path))
     result.append(dict(target=target,yaml=p,doc=doc,lockpath=lp,lock=lock,stage=sn,definition=stage,kind=kind,value=value,path=path))
 return result

def record_file(p,path):
 rec=dict(path=path,hash='md5',md5=register(p),size=p.stat().st_size)
 if os.access(p,os.X_OK):rec['isexec']=True
 return rec

def adopt_audit():
 import csv,collections
 rows=list(csv.DictReader((ROOT/'experiments/43_repository_preservation/results/file-tracking-audit/not-tracked-project-files.csv').open()))
 git=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
 defs=definitions();owner_map={d['target']:d for d in defs};groups=collections.defaultdict(list);changed={};excluded=[];approved=[];ignores=[]
 for index,row in enumerate(rows):
  if index%1000==0:print('Reviewing',index,'/',len(rows),flush=True)
  name=row['path'];p=ROOT/name
  if name in git:continue
  if not p.exists():excluded.append(dict(path=name,reason='no longer present'));continue
  reason=approve(p)
  if reason:excluded.append(dict(path=name,reason=reason));continue
  approved.append(name)
  owners=[owner_map[a] for a in [p,*p.parents] if a in owner_map]
  if owners:
   d=max(owners,key=lambda d:len(str(d['target'])));changed[str(d['target'])]=d
  else:
   parts=Path(name).parts;parent=ROOT.joinpath(*parts[:2]) if parts[0]=='experiments' else ROOT/parts[0] if len(parts)>1 else ROOT
   groups[parent].append(p)
 for target,d in changed.items():
  p=d['target']; entries=[];size=0
  if p.is_dir():
   for f in sorted(p.rglob('*')):
    if not f.is_file():continue
    name=str(f.relative_to(ROOT));reason=approve(f)
    if reason or name in git:
     excluded.append(dict(path=name,reason=reason or 'Git tracked'));ignores.append('/'+name);continue
    entries.append(dict(md5=register(f),relpath=f.relative_to(p).as_posix()));size+=f.stat().st_size
   rec=dict(path=d['path'],hash='md5',md5=directory(entries),size=size,nfiles=len(entries))
  else:rec=record_file(p,d['path'])
  # Reload on each modification so multiple stages in one lock retain changes.
  lp=d['lockpath'];lock=yaml.safe_load(lp.read_text()) if lp.exists() else {'schema':'2.0','stages':{}}
  stage=lock.setdefault('stages',{}).setdefault(d['stage'],{'cmd':d['definition']['cmd']});stage['outs']=[x for x in stage.get('outs',[]) if x['path']!=d['path']]+[rec]
  lp.write_text(yaml.safe_dump(lock,sort_keys=False))
 for parent,files in groups.items():
  pointer=parent/'historical-files.dvc';existing=yaml.safe_load(pointer.read_text()) if pointer.exists() else {'outs':[]};by={x['path']:x for x in existing['outs']}
  for p in files:by[os.path.relpath(p,parent)]=record_file(p,os.path.relpath(p,parent))
  pointer.write_text(yaml.safe_dump({'outs':[by[k] for k in sorted(by)]},sort_keys=False))
  ig=parent/'.gitignore';old=ig.read_text() if ig.exists() else '';lines=set(old.splitlines());new=['/'+os.path.relpath(p,parent) for p in files if '/'+os.path.relpath(p,parent) not in lines]
  if new:ig.write_text(old.rstrip()+'\n'+'\n'.join(new)+'\n')
 if ignores:
  p=ROOT/'.dvcignore';p.write_text(p.read_text().rstrip()+'\n# Excluded private/Git files in adopted directories\n'+'\n'.join(sorted(set(ignores)))+'\n')
 plan=dict(objects=objects,approved_files=approved,updated_directory_outputs=list(changed),excluded=excluded)
 (STATE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(approved=len(approved),objects=len(objects),excluded=len(excluded),updated_outputs=list(changed)),indent=2))

def track(paths):
 # For historical/source inputs only. Pipeline outputs use their stage records.
 defs=definitions()
 for name in paths:
  p=Path(name).absolute();assert p.is_relative_to(ROOT)
  owners=[d for d in defs if p==d['target'] or p.is_relative_to(d['target']) or d['target'].is_relative_to(p)]
  if owners:raise ValueError('Existing pipeline output: adopt its lock record instead of adding overlapping pointers: '+name)
  if p.is_dir():
   entries=[];size=0
   for f in sorted(p.rglob('*')):
    if f.is_file():entries.append(dict(md5=register(f),relpath=f.relative_to(p).as_posix()));size+=f.stat().st_size
   rec=dict(path=p.name,hash='md5',md5=directory(entries),size=size,nfiles=len(entries))
  else:rec=record_file(p,p.name)
  p.with_name(p.name+'.dvc').write_text(yaml.safe_dump({'outs':[rec]},sort_keys=False))
  ig=p.parent/'.gitignore';old=ig.read_text() if ig.exists() else '';line='/'+p.name
  if line not in old.splitlines():ig.write_text(old.rstrip()+'\n'+line+'\n')
 (STATE/'plan.json').write_text(json.dumps(dict(objects=objects),indent=2)+'\n')


def stage_commit(spec):
 """Adopt existing outputs without executing a stage or copying data."""
 file,stage=spec.rsplit(':',1);yp=Path(file).absolute();defs=[d for d in definitions() if d['yaml']==yp and d['stage']==stage]
 if not defs:raise ValueError('Stage not found: '+spec)
 lp=yp.with_name('dvc.lock');lock=yaml.safe_load(lp.read_text()) if lp.exists() else {'schema':'2.0','stages':{}}
 target=lock.setdefault('stages',{}).setdefault(stage,{'cmd':defs[0]['definition']['cmd']})
 replacements=[]
 for d in defs:
  if isinstance(d['value'],dict) and d['value'][d['path']].get('cache') is False:continue
  p=d['target']
  if p.is_dir():
   entries=[];size=0
   for f in sorted(p.rglob('*')):
    if f.is_file():entries.append(dict(md5=register(f),relpath=f.relative_to(p).as_posix()));size+=f.stat().st_size
   replacements.append(dict(path=d['path'],hash='md5',md5=directory(entries),size=size,nfiles=len(entries)))
  else:replacements.append(record_file(p,d['path']))
 replace={x['path'] for x in replacements};target['outs']=[x for x in target.get('outs',[]) if x['path'] not in replace]+replacements
 lp.write_text(yaml.safe_dump(lock,sort_keys=False));(STATE/'plan.json').write_text(json.dumps(dict(objects=objects,stage=spec),indent=2)+'\n')

def plan_records(specs):
 """Build a fresh upload plan from committed-format pointers/locks, checking local bytes."""
 for spec in specs:
  if ':' in spec:
   name,stage=spec.rsplit(':',1);p=Path(name).absolute();doc=yaml.safe_load(p.read_text());definition=doc['stages'][stage];base=p.parent/definition.get('wdir','.')
   records=yaml.safe_load(p.with_name('dvc.lock').read_text())['stages'][stage].get('outs',[])
   uncached={next(iter(x)) for kind in ['outs','metrics','plots'] for x in definition.get(kind,[]) if isinstance(x,dict) and (next(iter(x.values())) or {}).get('cache') is False}
   records=[x for x in records if x['path'] not in uncached]
  else:
   p=Path(spec).absolute();base=p.parent
   if p.suffix!='.dvc':raise ValueError('Expected .dvc pointer or dvc.yaml:stage')
   records=yaml.safe_load(p.read_text()).get('outs',[])
  if not p.is_relative_to(ROOT):raise ValueError('Metadata outside repository')
  for rec in records:
   target=Path(os.path.abspath(base/rec['path']));expected=rec['md5']
   if not target.is_relative_to(ROOT):raise ValueError('Output outside repository')
   if expected.endswith('.dir'):
    local=STATE/'metadata'/expected
    if local.exists():data=local.read_bytes()
    else:
     response=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+expected[:2]+'/'+expected[2:],timeout=90);response.raise_for_status();data=response.content
    assert hashlib.md5(data).hexdigest()==expected[:-4]
    entries=json.loads(data)
    for entry in entries:
     rel=Path(entry['relpath']);assert not rel.is_absolute() and '..' not in rel.parts
     assert register(target/rel)==entry['md5'],'Changed output: '+str(target/rel)
    assert directory(entries)==expected
   else:assert register(target)==expected,'Changed output: '+str(target)
 (STATE/'plan.json').write_text(json.dumps(dict(objects=objects,records=specs),indent=2)+'\n')
 print('Planned verified local objects:',len(objects))

def restore_records(records,destination):
 """Use standard DVC pull on scoped pointers without loading unrelated pipelines."""
 import shutil
 destination=destination.absolute()
 if not destination.is_relative_to(ROOT):raise ValueError('Restore destination must be below the repository')
 if destination.exists() and any(destination.iterdir()):raise ValueError('Restore destination must be empty')
 outputs=[]
 for name in records:
  pointer=Path(name).absolute()
  if not pointer.is_relative_to(ROOT) or pointer.suffix!='.dvc':raise ValueError('Expected a repository .dvc pointer')
  for output in yaml.safe_load(pointer.read_text()).get('outs',[]):
   target=Path(os.path.abspath(pointer.parent/output['path']))
   if not target.is_relative_to(ROOT):raise ValueError('Output outside repository')
   outputs.append({**output,'path':str(target.relative_to(ROOT))})
 destination.mkdir(parents=True,exist_ok=True)
 dvc=str(ROOT/'.venv/bin/dvc')
 subprocess.run([dvc,'init','--no-scm'],cwd=destination,check=True)
 shutil.copyfile(ROOT/'.dvc/config',destination/'.dvc/config')
 subprocess.run([dvc,'config','cache.type','hardlink,copy'],cwd=destination,check=True)
 (destination/'restoration.dvc').write_text(yaml.safe_dump({'outs':outputs},sort_keys=False))
 subprocess.run([dvc,'pull','restoration.dvc','-j','8'],cwd=destination,check=True)
 checked=0
 for output in outputs:
  p=destination/output['path'];expected=output['md5']
  if expected.endswith('.dir'):
   manifest=destination/'.dvc/cache/files/md5'/expected[:2]/expected[2:]
   assert hashlib.md5(manifest.read_bytes()).hexdigest()==expected[:-4]
   for entry in json.loads(manifest.read_bytes()):assert digest(p/entry['relpath'])[0]==entry['md5'];checked+=1
  else:assert digest(p)[0]==expected;checked+=1
 proof=dict(passed=True,restored_files=checked,records=records,method='Unmodified installed DVC pull with independent MD5 checks',destination=str(destination))
 (STATE/'restore-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
 p=sub.add_parser('push');p.add_argument('--plan',type=Path,default=STATE/'plan.json')
 p=sub.add_parser('plan');p.add_argument('records',nargs='+')
 sub.add_parser('adopt-audit');p=sub.add_parser('track');p.add_argument('paths',nargs='+')
 p=sub.add_parser('commit');p.add_argument('stage',help='path/to/dvc.yaml:stage')
 p=sub.add_parser('restore');p.add_argument('--destination',type=Path,required=True);p.add_argument('records',nargs='+')
 a=parser.parse_args()
 if a.command=='push':upload(a.plan)
 elif a.command=='plan':plan_records(a.records)
 elif a.command=='adopt-audit':adopt_audit()
 elif a.command=='commit':stage_commit(a.stage)
 elif a.command=='restore':restore_records(a.records,a.destination)
 else:track(a.paths)
