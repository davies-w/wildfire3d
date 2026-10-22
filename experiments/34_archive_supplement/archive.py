"""Preserve existing evidence omitted by historical DVC stage outputs; never rerun solvers."""
import json,tarfile,hashlib
from pathlib import Path
import yaml
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;selected=[]
for d in sorted((R/'experiments').iterdir()):
 if d.name[:2] not in [str(i) for i in range(17,27)]:continue
 roots=[]
 for p in d.rglob('dvc.lock'):
  if 'data' in p.relative_to(d).parts:continue
  for s in (yaml.safe_load(p.read_text()) or {}).get('stages',{}).values():
   roots.extend((p.parent/o['path']).resolve() for o in s.get('outs',[]) if o.get('md5'))
 for p in d.rglob('*.dvc'):
  roots.extend((p.parent/o['path']).resolve() for o in (yaml.safe_load(p.read_text()) or {}).get('outs',[]))
 for p in (d/'data').rglob('*'):
  if not p.is_file() or p.suffix in ['.lock','.pid','.dvc'] or '__pycache__' in p.parts:continue
  if any(p==o or o in p.parents for o in roots):continue
  selected.append(p)
manifest=[]
with tarfile.open(E/'data/supplement.tar','w') as t:
 for p in sorted(selected):
  name=str(p.relative_to(R));t.add(p,arcname=name,recursive=False)
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  manifest.append(dict(path=name,bytes=p.stat().st_size,sha256=h.hexdigest()))
(E/'manifest.json').write_text(json.dumps(dict(scope='Existing untracked-by-DVC evidence from experiments17-26; excludes runtime locks/PIDs and Python caches. Original paths retained in tar.',files=manifest),indent=2)+'\n')
print(len(manifest),'files',sum(x['bytes'] for x in manifest),'bytes')
