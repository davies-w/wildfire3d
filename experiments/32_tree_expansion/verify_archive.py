"""Verify locally archived raw bundles against existing cloud worker SHA256 records."""
import hashlib,json
from pathlib import Path
R=Path(__file__).parent;root=R/'data/cloud_archive';checked=[];errors=[]
for p in sorted(root.rglob('*.summary.json')):
 m=json.loads(p.read_text());h=m.get('raw_sha256')
 if not h:continue
 raw=p.with_name(p.name.replace('.summary.json','.tar.gz'))
 if not raw.exists():errors.append(str(raw));continue
 digest=hashlib.file_digest(raw.open('rb'),'sha256').hexdigest()
 if digest!=h:errors.append(str(raw))
 checked.append(dict(path=str(raw.relative_to(root)),sha256=digest))
(R/'results/cloud-archive-verified.json').write_text(json.dumps(dict(verified=not errors,raw_bundles=len(checked),errors=errors,files=checked),indent=2));assert not errors
print('Verified raw bundles',len(checked))
