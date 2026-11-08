"""Read-only file-by-file Git HEAD and DVC-output audit. Reports stay local/private."""
from pathlib import Path
import os,json,csv,hashlib,subprocess,collections,concurrent.futures,requests,yaml,time
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'experiments/43_repository_preservation/results/file-tracking-audit';REPORT.mkdir(parents=True,exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
git={}
for item in subprocess.check_output(['git','ls-tree','-rz','--full-tree',head],cwd=ROOT).split(b'\0'):
 if item:
  meta,name=item.split(b'\t',1);mode,kind,digest=meta.decode().split();git[os.fsdecode(name)]=(mode,digest)
def committed(n):return subprocess.check_output(['git','show',head+':'+n],cwd=ROOT)
def norm(base,name):return Path(os.path.abspath(base/name))
def rel(p):return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
outputs=[];deps=set();problems=[]
for name in sorted(git):
 if not (name.endswith('/dvc.lock') or name=='dvc.lock' or name.endswith('.dvc')):continue
 p=ROOT/name;doc=yaml.safe_load(committed(name));pointer=name.endswith('.dvc');pipe={} if pointer else yaml.safe_load(committed(str(p.with_name('dvc.yaml').relative_to(ROOT)))) if str(p.with_name('dvc.yaml').relative_to(ROOT)) in git else {}
 for sn,stage in ([('',doc)] if pointer else doc.get('stages',{}).items()):
  definition=doc if pointer else pipe.get('stages',{}).get(sn.split('@')[0]);stale=definition is None;definition=definition or {};definition=definition.get('do',definition);base=norm(p.parent,definition.get('wdir','.'))
  configs={}
  for kind in ['outs','metrics','plots']:
   for v in definition.get(kind,[]):
    if isinstance(v,str):configs[v]={}
    elif isinstance(v,dict):configs.update(v)
  for d in stage.get('deps',[]):deps.add(rel(norm(base,d['path'])))
  if stale:problems.append(dict(record=name,stage=sn,problem='lock stage absent from current dvc.yaml'))
  for o in stage.get('outs',[]):
   target=norm(base,o['path']);d=o.get('md5');outputs.append(dict(path=rel(target),absolute=str(target),md5=d,record=name,stage=sn,stale=stale,cached=configs.get(o['path'],{}).get('cache',True),exists=target.exists()))
local={}
for base in [ROOT/'.dvc/cache/files/md5',ROOT/'experiments/43_repository_preservation/data/private/storage-cleanup/nonpublic-objects']:
 if base.exists():
  for p in base.glob('*/*.dir'):local[p.parent.name+p.name]=p
special=ROOT/'experiments/43_repository_preservation/results/private-storage-directory.json'
if special.exists():local[hashlib.md5(special.read_bytes()).hexdigest()+'.dir']=special
wanted={o['md5'] for o in outputs if o['exists'] and o['md5'] and o['md5'].endswith('.dir')}
( REPORT/'directory-metadata').mkdir(exist_ok=True)
def getdir(h):
 try:
  if h in local:b=local[h].read_bytes()
  else:
   q=REPORT/'directory-metadata'/h
   if q.exists():b=q.read_bytes()
   else:
    v=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:],timeout=90);v.raise_for_status();b=v.content;q.write_bytes(b)
  assert hashlib.md5(b).hexdigest()==h[:-4];return h,json.loads(b),None
 except Exception as e:return h,None,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:directory_results=list(pool.map(getdir,sorted(wanted)))
directories={h:v for h,v,e in directory_results if e is None};unresolved={h:e for h,v,e in directory_results if e}
records=collections.defaultdict(list);unknown_roots=[];dir_roots=[]
for o in outputs:
 if not o['md5']:problems.append(dict(record=o['record'],stage=o['stage'],problem='output has no MD5'));continue
 if o['md5'].endswith('.dir'):
  if not o['exists']:continue
  dir_roots.append(o['path'])
  if o['md5'] not in directories:unknown_roots.append(o['path']);continue
  for e in directories[o['md5']]:
   n=rel(norm(Path(o['absolute']),e['relpath']));records[n].append({**o,'expected':e['md5']})
 else:records[o['path']].append({**o,'expected':o['md5']})
print('Git files',len(git),'DVC output entries',len(outputs),'directory manifests',len(directories),'unresolved',len(unresolved),flush=True)
files=[]
for base,ds,ns in os.walk(ROOT,followlinks=False):
 b=Path(base)
 if b==REPORT:ds[:]=[];continue
 for d in list(ds):
  if (b/d).is_symlink():files.append(b/d);ds.remove(d)
 for n in ns:files.append(b/n)
files.sort();memo={};counts=collections.Counter();bytes_by=collections.Counter();groups=collections.Counter();rows=[];start=time.time()
saved=REPORT/'verified-hash-cache.json'
if saved.exists():memo.update({tuple(k):tuple(v) for k,v in json.loads(saved.read_text())})
def hashes(p):
 st=p.lstat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 if key in memo:return memo[key]
 md=hashlib.md5();gh=hashlib.sha1();gh.update(b'blob '+str(st.st_size).encode()+b'\0')
 if p.is_symlink():
  b=os.fsencode(os.readlink(p));md.update(b);gh=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b)
 else:
  with p.open('rb') as f:
   while b:=f.read(8*1024*1024):md.update(b);gh.update(b)
 after=p.lstat();assert (after.st_size,after.st_mtime_ns)==(st.st_size,st.st_mtime_ns),'file changed during audit'
 memo[key]=(md.hexdigest(),gh.hexdigest());return memo[key]
for i,p in enumerate(files):
 name=str(p.relative_to(ROOT))
 try:size=p.lstat().st_size
 except FileNotFoundError:
  # Transfers may remove verified staging copies after this inventory was taken.
  # This observation is unresolved, not evidence of a verified backup or loss.
  rows.append(dict(path=name,bytes=0,status='disappeared_during_audit',category='project_file',dvc_records='',note='Absent after inventory; reconcile transfer receipt independently. Size unknown.'))
  counts['disappeared_during_audit']+=1
  continue
 recs=records.get(name,[]);active=[x for x in recs if not x['stale']];note='';matches=[]
 if name.startswith('.git/'):status='git_internal'
 elif name in git:
  try:_,gh=hashes(p);status='git_exact' if gh==git[name][1] else 'git_modified'
  except Exception as e:status='unverifiable';note=str(e)
 elif active:
  try:
   md,_=hashes(p);matches=[x for x in active if x['expected']==md];status='dvc_exact' if matches else 'dvc_modified'
   if matches and not any(x['cached'] for x in matches):status='dvc_uncached_output'
  except Exception as e:status='unverifiable';note=str(e)
 elif recs:status='stale_lock_only'
 elif any(name==x or name.startswith(x+'/') for x in unknown_roots):status='dvc_membership_unresolved'
 else:
  status='not_tracked';note='dependency only (not a stored output)' if name in deps else 'not listed in directory manifest' if any(name.startswith(x+'/') for x in dir_roots) else ''
 kind='environment_or_generated' if name.startswith(('.venv/','.dvc/','.artifact-staging/')) or '/__pycache__/' in name else 'project_file'
 refs=';'.join(sorted({x['record']+':'+x['stage'] for x in recs}));row=dict(path=name,bytes=size,status=status,category=kind,dvc_records=refs,note=note);rows.append(row);counts[status]+=1;bytes_by[status]+=size
 if status=='not_tracked':groups['/'.join(name.split('/')[:2])]+=1
 if i%10000==0:print('Audited',i,'/',len(files),'elapsed',round(time.time()-start),flush=True)
def write(name,values):
 with (REPORT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['path','bytes','status','category','dvc_records','note']);w.writeheader();w.writerows(values)
write('all-files.csv',rows);write('not-tracked.csv',[r for r in rows if r['status']=='not_tracked']);write('not-tracked-project-files.csv',[r for r in rows if r['status']=='not_tracked' and r['category']=='project_file']);write('modified-or-unresolved.csv',[r for r in rows if r['status'] not in ['git_exact','dvc_exact','not_tracked','git_internal']])
missing_git=[n for n in git if not (ROOT/n).exists() and not (ROOT/n).is_symlink()]
summary=dict(git_head=head,inventory_files=len(rows),counts=dict(counts),logical_bytes_by_status=dict(bytes_by),untracked_groups=dict(groups.most_common()),dvc_output_entries=len(outputs),directory_manifests_verified=len(directories),unresolved_directory_manifests=unresolved,stale_or_invalid_stage_records=problems,missing_git_files=missing_git,missing_dvc_outputs=[o for o in outputs if not o['exists']],scope='Every file and symlink within repository; directory symlinks are not traversed. Git internals included but classified separately. Report directory excluded as generated after inventory. Git HEAD contents are authoritative; DVC dependencies alone do not count as stored outputs. Exact DVC membership requires verified directory MD5. Remote artifact bytes were not re-audited by this script.')
(REPORT/'verified-hash-cache.json').write_text(json.dumps([[list(k),v] for k,v in memo.items()]));(REPORT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:summary[k] for k in ['inventory_files','counts','untracked_groups','directory_manifests_verified']},indent=2),flush=True)
