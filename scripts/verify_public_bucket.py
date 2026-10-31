"""Verify every public archive object by remote size and Xet content hash."""
from pathlib import Path
import json,hashlib,requests
from huggingface_hub import HfApi
import hf_xet
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'experiments/38_history8_shared64'
a=json.loads((E/'results08/public-model-upload.json').read_text());staging=Path(a['staging']);objects=a['objects'];paths=['wildfire3d/files/md5/'+h[:2]+'/'+h[2:] for h in objects]
remote={x.path:x for x in HfApi().get_bucket_paths_info('wdavies/dvc_storage',paths,token=False)}
assert set(remote)==set(paths),'Missing remote objects'
print('All remote objects present',len(remote),flush=True)
for i in range(0,len(paths),1000):
 chunk=paths[i:i+1000];local=[staging/p.removeprefix('wildfire3d/') for p in chunk]
 hashes=hf_xet.hash_files([str(p) for p in local])
 for path,p,h in zip(chunk,local,hashes):
  got=remote[path];assert got.size==h.file_size and got.xet_hash==h.hash,path
 print('Verified content hashes',min(i+1000,len(paths)),flush=True)
h=a['public_output_md5'];url='https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:]
q=requests.get(url,timeout=60);q.raise_for_status();assert hashlib.md5(q.content).hexdigest()==h.removesuffix('.dir')
proof={'passed':True,'objects':len(paths),'all_remote_sizes_and_xet_hashes_match':True,'anonymous_directory_readback_md5':h,'bucket':'wdavies/dvc_storage','scope':'Project-wide public model/data export; budget and credential exclusions applied'}
(E/'results08/public-model-remote-verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
