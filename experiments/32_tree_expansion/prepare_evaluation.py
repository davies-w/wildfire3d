"""Package frozen evidence and CPU-only evaluation on the existing bounded cloud image."""
from pathlib import Path
import json,tarfile,hashlib,io,base64,yaml
R=Path(__file__).parent
def main():
 assert json.loads((R/'results/test-simulations-complete.json').read_text())['complete']
 freeze=json.loads((R/'results/prediction-freeze.json').read_text());names=[n for n in freeze['files'] if not n.endswith('.npz')]
 names+=['results/prediction-freeze.json','evaluate_cloud.py','preprocess_cloud.py','fields.py','material_reader.py','fortran_records.py','alignment.py','original_cnn.py','previous_loss.py','groups.json']
 groups=json.loads((R/'groups.json').read_text());(R/'test-executions.json').write_text(json.dumps({g['id']:json.loads((R/'jobs'/g['id']/'execution.json').read_text()) for g in groups if g['phase']=='test'},indent=2));names+=['test-executions.json'];hashes={}
 with tarfile.open(R/'data/evaluation-overlay.tar','w') as tar:
  for n in sorted(set(names)):
   p=R/n;h=hashlib.sha256(p.read_bytes()).hexdigest()
   if n in freeze['files']:assert h==freeze['files'][n]
   hashes[n]=h;tar.add(p,arcname=n)
  raw=json.dumps(hashes).encode();ti=tarfile.TarInfo('evaluation-hashes.json');ti.size=len(raw);tar.addfile(ti,io.BytesIO(raw))
 (R/'results/evaluation-input-freeze.json').write_text(json.dumps(hashes,indent=2))
 source="""import urllib.request,urllib.parse,json,tarfile,pathlib,sys,runpy,hashlib,shutil
p=pathlib.Path('/tmp/study');p.mkdir(exist_ok=True);(p/'data').mkdir(exist_ok=True);(p/'results').mkdir(exist_ok=True)
r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
u='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/'+urllib.parse.quote('expansion32/evaluation01/overlay.tar',safe='')+'?alt=media'
with urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=180) as src,(p/'transfer.tar').open('wb') as dst:shutil.copyfileobj(src,dst,8*1024**2)
with tarfile.open(p/'transfer.tar') as tar:
 for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in pathlib.Path(m.name).parts and not m.issym() and not m.islnk()
 tar.extractall(p)
for n,h in json.loads((p/'evaluation-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
sys.path.insert(0,str(p));runpy.run_path(str(p/'evaluate_cloud.py'),run_name='__main__')
"""
 compile(source,'bootstrap','exec');w=yaml.safe_load((R/'gpu-workflow.yaml').read_text());a=w['main']['steps'][0]['initialize']['assign'];a[0]['deadline']='${sys.now() + 3000}';task=a[1]['job']['taskGroups'][0]['taskSpec'];task['maxRunDuration']='1560s';a[1]['job']['allocationPolicy']['instances'][0]['policy']['bootDisk']['sizeGb']='60';task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(source.encode()).decode())+"),'bootstrap','exec'))"]
 raw=json.dumps(w).replace('gpu32-learning01','gpu32-evaluation01').replace('expansion32/gpu01/job-status.json','expansion32/evaluation01/job-status.json').replace('+ 9000','+ 1800');(R/'evaluation-workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False))
if __name__=='__main__':main()
