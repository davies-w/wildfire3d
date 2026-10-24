"""Prepare immutable inputs and bounded workflow, without submitting cloud work."""
import base64,hashlib,io,json,tarfile,yaml
from pathlib import Path
R=Path(__file__).parent
assert json.loads((R/'results/preflight.json').read_text())['passed']
files=list(R.glob('*.py'))+[R/'schema.json',R/'coverage-plan.json',R/'data/sequences.npz']+list((R/'data/resume').glob('*'))
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(R/'data/pilot-overlay.tar','w') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
 raw=json.dumps(hashes).encode();info=tarfile.TarInfo('hashes.json');info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
(R/'results/input-freeze.json').write_text(json.dumps(hashes,indent=2))
source="""import pathlib,sys,runpy,urllib.request,urllib.parse,json,tarfile,shutil,hashlib
p=pathlib.Path('/tmp/study');p.mkdir(exist_ok=True)
r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
u='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/'+urllib.parse.quote('diagnostics35/attempt15/pilot-overlay.tar',safe='')+'?alt=media'
with urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=180) as src,(p/'transfer.tar').open('wb') as dst:shutil.copyfileobj(src,dst)
with tarfile.open(p/'transfer.tar') as tar:
 for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in pathlib.Path(m.name).parts and not m.issym() and not m.islnk()
 tar.extractall(p)
for n,h in json.loads((p/'hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
(p/'results').mkdir(exist_ok=True);sys.path.insert(0,str(p));
try:
 runpy.run_path(str(p/'worker.py'),run_name='__main__')
except BaseException:
 import traceback
 from runtime import upload
 upload('bootstrap-error.txt',traceback.format_exc().encode());raise
"""
compile(source,'bootstrap','exec')
w=yaml.safe_load((R.parent.parent/'32_tree_expansion/gpu-workflow.yaml').read_text());raw=json.dumps(w).replace('gpu32-learning01','gpu35-min15').replace('expansion32/gpu01/job-status.json','diagnostics35/attempt15/job-status.json').replace('+ 10800','+ 12600').replace('+ 9000','+ 11100').replace('8400s','10800s');w=json.loads(raw.replace('us-central1-a','us-central1-c'))
job=w['main']['steps'][0]['initialize']['assign'][1]['job'];job['allocationPolicy']['instances'][0]['policy']['provisioningModel']='STANDARD';job['allocationPolicy']['instances'][0]['policy']['bootDisk']['sizeGb']='60';job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(source.encode()).decode())+"),'bootstrap','exec'))"]
(R/'gpu-workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
(R/'results/prepared.json').write_text(json.dumps(dict(submitted=False,overlay_bytes=(R/'data/pilot-overlay.tar').stat().st_size,overlay_sha256=hashlib.sha256((R/'data/pilot-overlay.tar').read_bytes()).hexdigest(),proposed_new_cap_usd=3,estimated_usd=[0.5,1.2],task_deadline_s=10800,vm_age_limit_s=11100,absolute_deadline_s=12600,queue_limit_s=1200,automatic_retries=0),indent=2))
print('Prepared; no cloud submission')
