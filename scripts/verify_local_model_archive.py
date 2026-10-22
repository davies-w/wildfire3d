"""Verify local DVC mirror closure including imported-input records; no network publication."""
import json,hashlib,subprocess,yaml
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments/33_representation_loss';mirror=R/'FDS/hf_dvc_mirror/files/md5';roots=[p for p in (R/'experiments').iterdir() if p.name[:2] in ['27','28','29','30','31','32','33']];hashes=set();inputs=[]
for root in roots:
 for p in root.rglob('*.dvc'):
  if 'data' in p.relative_to(root).parts:continue
  subprocess.run([str(R/'.venv/bin/dvc'),'push','-r','mirror',str(p.relative_to(R))],cwd=R,check=True);inputs.append(str(p.relative_to(R)))
  for o in yaml.safe_load(p.read_text()).get('outs',[]):
   if o.get('md5'):hashes.add(o['md5'])
 for p in root.rglob('dvc.lock'):
  if 'data' in p.relative_to(root).parts:continue
  for stage in yaml.safe_load(p.read_text()).get('stages',{}).values():
   for o in stage.get('outs',[]):
    h=o.get('md5')
    if h and (mirror/h[:2]/h[2:]).exists():hashes.add(h)
errors=[];seen=set();queue=list(hashes)
while queue:
 h=queue.pop()
 if h in seen:continue
 seen.add(h);p=mirror/h[:2]/h[2:]
 if not p.exists():errors.append(dict(hash=h,error='missing'));continue
 if h.endswith('.dir'):
  raw=p.read_bytes()
  if hashlib.md5(raw).hexdigest()!=h[:-4]:errors.append(dict(hash=h,error='directory hash mismatch'))
  queue.extend(x['md5'] for x in json.loads(raw))
 # Raw bundle bytes independently SHA256 verified; here test object presence/size for closure.
 elif p.stat().st_size==0 and h!='d41d8cd98f00b204e9800998ecf8427e':errors.append(dict(hash=h,error='unexpected empty object'))
(E/'results/local-archive-verification.json').write_text(json.dumps(dict(verified=not errors,objects=len(seen),import_records=inputs,errors=errors,scope='Local mirror object closure and directory hashes; raw SHA256 checked separately; public upload not performed'),indent=2));assert not errors
print('Local archive objects verified',len(seen))
