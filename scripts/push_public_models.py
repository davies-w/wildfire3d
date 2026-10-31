"""Upload only the reviewed public-model DVC output, never the whole mirror."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,yaml
ROOT=Path(__file__).resolve().parents[1];subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/verify_public_models.py')],check=True);E=ROOT/'experiments/38_history8_shared64';mirror=ROOT/'FDS/hf_dvc_mirror/files/md5'
lock=yaml.safe_load((E/'dvc.lock').read_text());h=lock['stages']['export_public_models']['outs'][0]['md5'];seen=set();staging=Path(tempfile.mkdtemp(prefix='fire-public-model-dvc-'))
def add(h):
 if h in seen:return
 p=mirror/h[:2]/h[2:];b=p.read_bytes();assert hashlib.md5(b).hexdigest()==h.removesuffix('.dir'),p
 seen.add(h);out=staging/'files/md5'/h[:2]/h[2:];out.parent.mkdir(parents=True,exist_ok=True);os.link(p,out)
 if h.endswith('.dir'):
  for x in json.loads(b):add(x['md5'])
add(h)
(staging/'model-archive.json').write_text(json.dumps({'dvc_output':'experiments/38_history8_shared64/data/project-model-archive','directory_md5':h,'directory_url':'https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:],'policy':'Project-wide model/checkpoint and numerical dataset export. Budgets and private keys excluded.'},indent=2))
print(json.dumps({'public_output_md5':h,'objects':len(seen),'staging':str(staging),'bytes':sum(p.stat().st_size for p in staging.rglob('*') if p.is_file())}),flush=True)
subprocess.run([str(ROOT/'.venv/bin/hf'),'buckets','sync',str(staging),'hf://buckets/wdavies/dvc_storage/wildfire3d','--no-delete','--ignore-times'],check=True)
(E/'results08/public-model-upload.json').write_text(json.dumps({'public_output_md5':h,'objects':sorted(seen),'bucket':'wdavies/dvc_storage','prefix':'wildfire3d','staging':str(staging)},indent=2))
