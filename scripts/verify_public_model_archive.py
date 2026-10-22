"""Verify approved public archive presence/size and anonymous sampled content hashes."""
import json,hashlib,urllib.request,time
from pathlib import Path
from huggingface_hub import HfApi
R=Path(__file__).resolve().parents[1];mirror=R/'FDS/hf_dvc_mirror';E=R/'experiments/33_representation_loss';prefix='wildfire3d/'
remote={x.path:x for x in HfApi().list_bucket_tree('wdavies/dvc_storage',prefix='wildfire3d',recursive=True) if x.type=='file'}
files=[p for p in mirror.rglob('*') if p.is_file()];errors=[]
for p in files:
 key=prefix+p.relative_to(mirror).as_posix();item=remote.get(key)
 if item is None or item.size!=p.stat().st_size:errors.append(key)
assert not errors, f'Missing/wrong-sized objects: {errors[:10]}'
candidates=sorted([p for p in files if p.stat().st_size<10_000_000 and not p.name.endswith('.dir')],key=lambda p:p.stat().st_size,reverse=True)[:6];samples=[]
for p in candidates:
 key=prefix+p.relative_to(mirror).as_posix();url='https://huggingface.co/buckets/wdavies/dvc_storage/resolve/'+key
 with urllib.request.urlopen(url,timeout=180) as src:raw=src.read()
 assert hashlib.sha256(raw).digest()==hashlib.sha256(p.read_bytes()).digest(),key
 samples.append(dict(path=key,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
proof=dict(verified=True,objects=len(files),bytes=sum(p.stat().st_size for p in files),anonymous_hash_samples=samples,verified_unix=time.time(),scope='All local mirror object paths/sizes match remote; six anonymous downloads SHA256 match. Raw bundles independently SHA256 verified locally; not every remote byte re-downloaded.')
(E/'results/public-archive-verification.json').write_text(json.dumps(proof,indent=2));status=json.loads((E/'results/archive-status.json').read_text());status['public_upload']='complete and verified';(E/'results/archive-status.json').write_text(json.dumps(status,indent=2));print('PUBLIC ARCHIVE VERIFIED',len(files))
