"""Audit then remove exactly four authorized redundant directories, inside this repo."""
from pathlib import Path
import os,json,hashlib,shutil,argparse
ROOT=Path(__file__).resolve().parents[1]
TARGETS=['experiments/43_repository_preservation/data/public','experiments/38_history8_shared64/data/project-model-archive','.dvc/cache','FDS/hf_dvc_mirror']
E=ROOT/'experiments/43_repository_preservation';OUT=E/'data/private/storage-cleanup';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--delete',action='store_true');args=parser.parse_args()
def inside(p):
 return any(p==ROOT/t or ROOT/t in p.parents for t in TARGETS)
def save(p,rel):
 dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():os.link(p,dest)
 return dest
if not args.delete:
 proof=json.loads((E/'public-verification.json').read_text());assert proof['passed'] and proof['every_remote_hash_verified']
 m=json.loads((E/'data/public/manifest.json').read_text());assert m['distinct_historical_model_data_versions']==0
 shutil.copy2(E/'data/public/manifest.json',OUT/'public-manifest.json')
 archive=ROOT/TARGETS[1];shutil.copy2(archive/'manifest.json',OUT/'model-archive-manifest.json')
 public={r['md5'] for r in m['files']};public.add(proof['directory_md5']);public.add(hashlib.md5((E/'data/public/manifest.json').read_bytes()).hexdigest())
 missing=[]
 for row in m['files']:
  source=ROOT/row.get('source',row['path'])
  if not source.is_file() or inside(source):
   save(E/'data/public'/row['path'],'retained-export-files/'+row['path']);missing.append(row['path'])
 # Preserve any historical/private cache object not covered by verified public upload.
 retained={}
 for folder in [ROOT/'.dvc/cache/files/md5',ROOT/'FDS/hf_dvc_mirror/files/md5']:
  for prefix in folder.iterdir():
   if not prefix.is_dir():continue
   for p in prefix.iterdir():
    if not p.is_file():continue
    h=prefix.name+p.name
    if h not in public:
     save(p,'nonpublic-objects/'+prefix.name+'/'+p.name);retained[h]=p.stat().st_size
 # Keep legacy cache layouts and run-cache provenance, which are not in the public graph.
 for child in (ROOT/'.dvc/cache').iterdir():
  if child.name=='files':continue
  if child.is_dir():
   for p in child.rglob('*'):
    if p.is_file():save(p,'legacy-cache/'+str(p.relative_to(ROOT/'.dvc/cache')))
  elif child.is_file():save(child,'legacy-cache/'+child.name)
 # Record every retained file; refuse deletion if any symlink resolves into targets.
 files=[];links=[]
 for base,dirs,names in os.walk(ROOT,followlinks=False):
  b=Path(base);dirs[:]=[d for d in dirs if d not in ['.git','.venv','__pycache__'] and not inside(b/d) and b/d!=OUT]
  for d in dirs:
   p=b/d
   if p.is_symlink() and inside(p.resolve()):links.append(str(p.relative_to(ROOT)))
  for n in names:
   p=b/n
   if inside(p) or p==Path(__file__):continue
   if p.is_symlink():
    if inside(p.resolve()):links.append(str(p.relative_to(ROOT)))
    continue
   st=p.stat();files.append([str(p.relative_to(ROOT)),st.st_size,st.st_mtime_ns,st.st_ino])
 report=dict(targets=TARGETS,retained_files=files,blocking_symlinks=links,retained_nonpublic_objects=len(retained),retained_nonpublic_bytes=sum(retained.values()),retained_missing_source_exports=missing,free_bytes_before=shutil.disk_usage(ROOT).free)
 (OUT/'plan.json').write_text(json.dumps(report));print({k:v for k,v in report.items() if k not in ['retained_files','retained_missing_source_exports']},flush=True);print('Retained files',len(files),'missing-source exports',len(missing))
else:
 report=json.loads((OUT/'plan.json').read_text());assert report['targets']==TARGETS and not report['blocking_symlinks']
 def verify():
  for name,size,mtime,inode in report['retained_files']:
   p=ROOT/name;s=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(size,mtime,inode),name
 verify()
 for name in TARGETS:
  p=ROOT/name;assert p.is_dir() and not p.is_symlink() and ROOT in p.resolve().parents
  print('Removing',name,flush=True);shutil.rmtree(p)
 verify();report.pop('retained_files');report['retained_files_unchanged']=True;report['free_bytes_after']=shutil.disk_usage(ROOT).free;report['reclaimed_bytes']=report['free_bytes_after']-report['free_bytes_before'];(OUT/'completed.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
