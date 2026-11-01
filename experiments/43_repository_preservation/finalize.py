"""Final privacy and completeness pass before adopting the snapshot."""
from pathlib import Path
import json,hashlib,re,tarfile,ctypes,os,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
# Reuse only definitions, never rerun the full scan on import.
ns={'__file__':str(R/'audit.py')};exec((R/'audit.py').read_text().split('paths=[]')[0],ns)
D=R/'data/public';manifest=json.loads((D/'manifest.json').read_text());rows=manifest['files'];excluded=manifest['excluded'];kept=[]
secret=ns['SECRET'];ledger=re.compile(r'(?:^|[-_])(?:budget|billing|invoice|spending)(?:[-_.]|$)',re.I)
for row in rows:
 p=D/row['path'];name=Path(row['path']).name;reason=None
 if ledger.search(name) and 'energy' not in name.lower() and p.suffix in ['.json','.lock','.csv']:reason='spending record excluded in final review'
 elif p.stat().st_size<=2*1024*1024 and secret.search(p.read_bytes()):reason='credential excluded in final review'
 if reason:
  p.unlink();excluded.append(dict(path=row['path'],reason=reason));continue
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
# Make immutable-by-identity CoW copies: never leave the public snapshot/cache
# hardlinked to mutable source files. APFS clones do not duplicate file data.
libc=ctypes.CDLL(None,use_errno=True);clone=libc.clonefile
clone.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];clone.restype=ctypes.c_int
def detach(p):
 t=p.with_name(p.name+'.audit-clone')
 if t.exists():t.unlink()
 if clone(os.fsencode(p),os.fsencode(t),0)!=0:raise OSError(ctypes.get_errno(),str(p))
 os.replace(t,p)
# The root ignore file was updated after scan; recover its old Git bytes if
# the earlier direct hardlink changed that now-obsolete cache entry.
old=next(v for v in manifest['files'] if v['path']=='.gitignore')
b=subprocess.check_output(['git','show','HEAD:.gitignore'],cwd=ROOT)
if hashlib.md5(b).hexdigest()==old['md5']:
 for base in [ns['cache'],ns['mirror']]:
  p=base/old['md5'][:2]/old['md5'][2:]
  if p.exists() and hashlib.md5(p.read_bytes()).hexdigest()!=old['md5']:
   p.unlink();p.write_bytes(b)
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
