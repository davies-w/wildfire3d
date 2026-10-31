"""Sync only this reviewed scientific input output; budgets/results excluded."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,yaml,argparse
from huggingface_hub import HfApi
import hf_xet,requests
R=Path(__file__).resolve().parent;ROOT=R.parents[1];mirror=ROOT/'FDS/hf_dvc_mirror/files/md5'
parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','prepare_pool02','progress','collect','analysis','public','reports'],default='prepare_pool02');args=parser.parse_args()
lock=yaml.safe_load((R/'dvc.lock').read_text());h=lock['stages'][args.stage]['outs'][0]['md5'];stage=Path(tempfile.mkdtemp(prefix='stacked42-public-'));objects={}
def add(digest):
 if digest in objects:return
 p=mirror/digest[:2]/digest[2:];b=p.read_bytes();assert hashlib.md5(b).hexdigest()==digest.removesuffix('.dir')
 dest=stage/'files/md5'/digest[:2]/digest[2:];dest.parent.mkdir(parents=True,exist_ok=True);os.link(p,dest);objects[digest]=dest
 if digest.endswith('.dir'):
  for e in json.loads(b):add(e['md5'])
add(h)
p=json.loads((R/'data/training02/coverage-plan.json').read_text());assert 'budget' not in p
assert all(not any(x in f.name.lower() for x in ['budget','credential','private_key']) for f in (R/'data/training02').rglob('*') if f.is_file())
subprocess.run([str(ROOT/'.venv/bin/hf'),'buckets','sync',str(stage),'hf://buckets/wdavies/dvc_storage/wildfire3d','--no-delete'],check=True)
paths=['wildfire3d/files/md5/'+v[:2]+'/'+v[2:] for v in objects]
found={v.path:v for v in HfApi().get_bucket_paths_info('wdavies/dvc_storage',paths,token=False)}
for path,hashed in zip(paths,hf_xet.hash_files([str(v) for v in objects.values()])):
 assert found[path].size==hashed.file_size and found[path].xet_hash==hashed.hash,path
url='https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:]
r=requests.get(url,timeout=90);r.raise_for_status();assert hashlib.md5(r.content).hexdigest()==h.removesuffix('.dir')
proof=dict(passed=True,directory_md5=h,objects=len(objects),remote_hashes_verified=True,anonymous_directory_readback=True)
(R/('public-artifact-verification02.json' if args.stage in ['prepare','prepare_pool02'] else 'public-'+args.stage+'-verification.json')).write_text(json.dumps(proof,indent=2)+'\n');print(proof)
