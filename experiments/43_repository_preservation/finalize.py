"""Final privacy and completeness pass before adopting the snapshot."""
from pathlib import Path
import json,hashlib,re,tarfile,ctypes,os,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
# Reuse only definitions, never rerun the full scan on import.
ns={'__file__':str(R/'audit.py')};exec((R/'audit.py').read_text().split('paths=[]')[0],ns)
D=R/'data/public';manifest=json.loads((D/'manifest.json').read_text());rows=manifest['files'];excluded=manifest['excluded'];kept=[]
# Installed engine/dependency trees are excluded, but project case outputs
# and ad-hoc scientific runs in the engine working area are artifacts too.
ns['rows']=rows;ns['exclusions']=excluded;known={v['path'] for v in rows};extra=0
for base in [ROOT/'FDS/cases',ROOT/'FDS/runs']:
 for source in sorted(base.rglob('*')):
  if source.is_file():
   name=str(source.relative_to(ROOT))
   if name not in known:ns['process'](source,name);known.add(name);extra+=1
for name in ['FDS/nofront.c','FDS/nofront.dylib','FDS/arm64_build.log']:
 if (ROOT/name).is_file() and name not in known:ns['process'](ROOT/name,name);extra+=1
manifest['engine_working_area_files']=extra
class FastSecret:
 def search(self,b):
  # Every regex alternative requires one of these literal prefixes. This
  # fast C-level prefilter preserves exactly the original matching rules.
  if not any(marker in b for marker in (b'-----BEGIN ',b'hf_',b'AIza',b'AKIA')):return None
  return ns['SECRET'].search(b)
secret=FastSecret();ledger=re.compile(r'(?:^|[-_])(?:budget|billing|invoice|spending)(?:[-_.]|$)',re.I)
for row in rows:
 p=D/row['path'];name=Path(row['path']).name;reason=None
 if name in {'cost.json','cost-reservations.json','job-reservation.json','cost-summary.json','cost-proxy.json','cost-console.txt'}:reason='spending record excluded in final review'
 if ledger.search(name) and 'energy' not in name.lower() and p.suffix in ['.json','.lock','.csv']:reason='spending record excluded in final review'
 if reason:
  if p.exists():p.unlink()
  excluded.append(dict(path=row['path'],reason=reason));continue
 assert p.exists(), 'Unexpected missing snapshot artifact: '+row['path']
 if p.stat().st_size<=2*1024*1024 and secret.search(p.read_bytes()):
  p.unlink();excluded.append(dict(path=row['path'],reason='credential excluded in final review'));continue
 if p.suffix.lower() in ['.tar','.tgz','.gz'] and tarfile.is_tarfile(p):
  with tarfile.open(p,'r:*') as tf:
   for m in tf:
    if m.isfile() and m.size<=2*1024*1024:
     assert not secret.search(tf.extractfile(m).read()),'Credential in packaged artifact; do not publish: '+row['path']
 kept.append(row)
# Include up-to-date reviewed source/documentation changed during the scan.
refresh=['.gitignore','experiments/37_integral_objective/README.md','experiments/38_history8_shared64/README.md']
kept=[v for v in kept if v['path'] not in refresh];ns['rows']=kept;ns['exclusions']=excluded
for name in refresh:ns['process'](ROOT/name,name)
# Keep genuinely different historical model/data versions from the previous
# public archive, while avoiding another copy of identical exports.
archive=ROOT/'experiments/38_history8_shared64/data/project-model-archive'
previous=json.loads((archive/'manifest.json').read_text())
current={v['path']:v for v in ns['rows']};historical=0
for row in previous['files']:
 if Path(row['path']).suffix.lower() not in {'.pt','.pth','.npz','.npy','.safetensors'}:continue
 now=current.get('experiments/'+row['path'])
 if now and now['sha256']==row['sha256']:continue
 source=archive/row['path'];assert source.is_file()
 assert ns['hashes'](source)[1]==row['sha256']
 ns['process'](source,'historical-model-archive/'+row['path']);historical+=1
manifest['distinct_historical_model_data_versions']=historical
# Make immutable-by-identity CoW copies: never leave the public snapshot/cache
# hardlinked to mutable source files. APFS clones do not duplicate file data.
libc=ctypes.CDLL(None,use_errno=True);clone=libc.clonefile
clone.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];clone.restype=ctypes.c_int
def detach(p):
 t=p.with_name(p.name+'.audit-clone')
 if t.exists():t.unlink()
 if clone(os.fsencode(p),os.fsencode(t),0)!=0:raise OSError(ctypes.get_errno(),str(p))
 os.replace(t,p)
seen=set()
for i,row in enumerate(ns['rows']):
 p=D/row['path'];detach(p);digest=row['md5']
 if digest not in seen:
  c=ns['cache']/digest[:2]/digest[2:];detach(c)
  m=ns['mirror']/digest[:2]/digest[2:];m.unlink();os.link(c,m);seen.add(digest)
 if i%10000==0:print('Isolated snapshot files',i,flush=True)
rows=ns['rows'];assert len({v['path'] for v in rows})==len(rows)
allowed={v['path'] for v in rows}|{'manifest.json'}
assert {str(p.relative_to(D)) for p in D.rglob('*') if p.is_file()}==allowed
manifest.update(files=rows,excluded=excluded,exported_files=len(rows),logical_bytes=sum(v['bytes'] for v in rows),unique_objects=len({v['md5'] for v in rows}))
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(R/'results/privacy-reviewed.json').write_text(json.dumps(dict(passed=True,files=len(rows),exclusions=len(excluded),credential_pattern_review=True),indent=2)+'\n')
print(dict(files=len(rows),unique_objects=manifest['unique_objects'],logical_bytes=manifest['logical_bytes'],exclusions=len(excluded)))
