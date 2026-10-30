"""Audit existing experiment artifacts against DVC lock and the private mirror."""
from pathlib import Path
import hashlib,json,yaml
R=Path(__file__).resolve().parent;root=R.parents[1];mirror=root/'FDS/hf_dvc_mirror/files/md5';lock=yaml.safe_load((R/'dvc.lock').read_text());seen=set();outs=[]
def check(h):
 if h in seen:return
 p=mirror/h[:2]/h[2:];assert p.is_file(),p
 b=p.read_bytes();assert hashlib.md5(b).hexdigest()==h.removesuffix('.dir'),p
 seen.add(h)
 if h.endswith('.dir'):
  for row in json.loads(b):check(row['md5'])
for stage in lock['stages'].values():
 for o in stage.get('outs',[]):
  p=R/o['path']
  if not p.exists():continue
  check(o['md5']);outs.append(o['path'])
  if p.is_dir():
   entries=json.loads((mirror/o['md5'][:2]/o['md5'][2:]).read_bytes());expected={x['relpath']:x['md5'] for x in entries}
   actual={str(f.relative_to(p)):hashlib.md5(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()};assert actual==expected,p
  else:assert hashlib.md5(p.read_bytes()).hexdigest()==o['md5'],p
uncovered=[str(p.relative_to(R)) for p in (R/'data').rglob('*') if p.is_file() and p.suffix!='.lock' and not any(str(p.relative_to(R))==o or str(p.relative_to(R)).startswith(o+'/') for o in outs)]
assert not uncovered,uncovered
for folder in ['results',*[f'results{i:02d}' for i in range(1,9)]]:
 for p in (R/folder).glob('*.json'):
  if p.name=='artifact-coverage.json':continue
  dest=R/'data/provenance01'/((folder+'-' if folder!='results' else '')+p.name)
  assert dest.is_file() and dest.read_bytes()==p.read_bytes(),p
print(json.dumps({'passed':True,'existing_outputs':len(outs),'verified_private_mirror_objects':len(seen),'uncovered_data_files':uncovered,'excluded_runtime_locks':['data/launch.lock','data/pair-sequence-collection.lock']}))
