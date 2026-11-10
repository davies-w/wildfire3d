"""Join two retained historical archive part sets and review contents; never delete sources."""
from pathlib import Path
import hashlib,json,shutil,tarfile
import dvc_hf as hf
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'experiments/51_three_tree_campaign/private07';out=p/'unmanifested-archive-review';out.mkdir(exist_ok=True)
results=[]
for case in ['tree48_000830_fine','tree48_001824_fine']:
 source=ROOT/'experiments/48_two_tree_design/private05/failed-cases/bulk'/case
 parts=sorted(source.glob('archive-*.tar.gz.part'));assert len(parts)==25;assert [x.name for x in parts]==[f'archive-{i:05d}.tar.gz.part' for i in range(25)]
 dest=out/(case+'.tar.gz');hashes=[]
 with dest.open('wb') as target:
  for part in parts:
   md,sha=hf.digest(part);hashes.append({'path':str(part.relative_to(ROOT)),'sha256':sha,'bytes':part.stat().st_size})
   with part.open('rb') as f:shutil.copyfileobj(f,target)
 # Exhausting the gzip stream checks integrity beyond tar's end-of-archive marker.
 import gzip
 with gzip.open(dest,'rb') as f:
  while f.read(8*1024*1024):pass
 with tarfile.open(dest,'r:gz') as t:members=sum(1 for _ in t)
 reason=hf.approve(dest);md,sha=hf.digest(dest);row={'path':str(dest.relative_to(ROOT)),'bytes':dest.stat().st_size,'md5':md,'sha256':sha,'public_policy_passed':reason is None,'exclusion_reason':reason};results.append(row)
 (out/(case+'-sources.json')).write_text(json.dumps({'parts':hashes,'tar_members':members,'archive_sha256':sha,'policy_reason':reason},indent=2)+'\n');print(case,'members',members,'policy',reason,flush=True)
(p/'unmanifested-archive-policy-review.json').write_text(json.dumps({'files':[x for x in results if x['public_policy_passed']],'excluded':[x for x in results if not x['public_policy_passed']]},indent=2)+'\n')
