"""Publish only the audited snapshot graph; verify every remote object."""
from pathlib import Path
import os,json,hashlib,tempfile,subprocess,yaml,requests
from huggingface_hub import HfApi
import hf_xet
R=Path(__file__).resolve().parent;ROOT=R.parents[1];cache=ROOT/'.dvc/cache/files/md5'
h=yaml.safe_load((R/'dvc.lock').read_text())['stages']['snapshot']['outs'][0]['md5']
manifest=json.loads((R/'data/public/manifest.json').read_text());objects={h:cache/h[:2]/h[2:]}
entries=json.loads(objects[h].read_text())
assert {e['relpath'] for e in entries}=={v['path'] for v in manifest['files']}|{'manifest.json'}
recorded={v['path']:v for v in manifest['files']}
assert all(e['relpath']=='manifest.json' or (e['md5']==recorded[e['relpath']]['md5']) for e in entries)
for e in entries:
 objects[e['md5']]=cache/e['md5'][:2]/e['md5'][2:]
 if e['relpath']!='manifest.json':assert objects[e['md5']].stat().st_size==recorded[e['relpath']]['bytes']
expected_sha={v['md5']:v['sha256'] for v in manifest['files']}
stage=Path(tempfile.mkdtemp(prefix='repo43-public-'));api=HfApi();items=list(objects.items());verified=0
for start in range(0,len(items),250):
 batch=items[start:start+250];paths=['wildfire3d/files/md5/'+d[:2]+'/'+d[2:] for d,p in batch]
 remote={v.path:v for v in api.get_bucket_paths_info('wdavies/dvc_storage',paths,token=False)}
 for (digest,p),path,xh in zip(batch,paths,hf_xet.hash_files([str(p) for d,p in batch])):
  md=hashlib.md5();sha=hashlib.sha256()
  with p.open('rb') as f:
   while b:=f.read(8*1024*1024):md.update(b);sha.update(b)
  assert md.hexdigest()==digest.removesuffix('.dir'),digest
  if digest in expected_sha:assert sha.hexdigest()==expected_sha[digest],digest
  v=remote.get(path)
  if v and v.size==xh.file_size and v.xet_hash==xh.hash:verified+=1;continue
  dest=stage/'files/md5'/digest[:2]/digest[2:];dest.parent.mkdir(parents=True,exist_ok=True);os.link(p,dest)
 if start%2500==0:print(json.dumps(dict(checked=start,already_verified=verified,total=len(items))),flush=True)
print('Uploading missing or mismatched objects',flush=True)
subprocess.run([str(ROOT/'.venv/bin/hf'),'buckets','sync',str(stage),'hf://buckets/wdavies/dvc_storage/wildfire3d','--no-delete'],check=True)
for start in range(0,len(items),250):
 batch=items[start:start+250];paths=['wildfire3d/files/md5/'+d[:2]+'/'+d[2:] for d,p in batch]
 remote={v.path:v for v in api.get_bucket_paths_info('wdavies/dvc_storage',paths,token=False)}
 for path,xh in zip(paths,hf_xet.hash_files([str(p) for d,p in batch])):
  v=remote[path];assert v.size==xh.file_size and v.xet_hash==xh.hash,path
 if start%2500==0:print('Verified',start,'/',len(items),flush=True)
response=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:],timeout=120);response.raise_for_status();assert hashlib.md5(response.content).hexdigest()==h.removesuffix('.dir')
proof=dict(passed=True,directory_md5=h,objects=len(items),files=len(entries),every_remote_hash_verified=True,anonymous_directory_readback=True)
(R/'public-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
