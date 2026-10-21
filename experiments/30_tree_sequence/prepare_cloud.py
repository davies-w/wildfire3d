from pathlib import Path
import json,yaml,base64,time
R=Path(__file__).parent;P=R.parent/'29_single_tree_heads/gpu_training'
bootstrap='''import urllib.request,json,tarfile,pathlib,sys,runpy,hashlib,shutil
p=pathlib.Path('/tmp/study');p.mkdir(exist_ok=True)
for obj,manifest in [('gpu29/train01/inputs.tar','input-hashes.json'),('gpu30/sequence01/overlay.tar','overlay-hashes.json')]:
 r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
 import urllib.parse
 url='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/'+urllib.parse.quote(obj,safe='')+'?alt=media'
 r=urllib.request.Request(url,headers={'Authorization':'Bearer '+token})
 with urllib.request.urlopen(r,timeout=180) as src,(p/'transfer.tar').open('wb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
 with tarfile.open(p/'transfer.tar') as f:
  for m in f.getmembers():assert not m.name.startswith('/') and '..' not in pathlib.PurePosixPath(m.name).parts and not m.issym() and not m.islnk()
  f.extractall(p)
 for n,h in json.loads((p/manifest).read_text()).items():
  dig=hashlib.sha256()
  with (p/n).open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):dig.update(b)
  assert dig.hexdigest()==h,n
sys.path.insert(0,str(p));runpy.run_path(str(p/'worker.py'),run_name='__main__')'''
compile(bootstrap,'bootstrap','exec');w=yaml.safe_load((P/'workflow02.yaml').read_text());a=w['main']['steps'][0]['initialize']['assign'];a[0]['deadline']='${sys.now() + 3300}';task=a[1]['job']['taskGroups'][0]['taskSpec'];task['maxRunDuration']='1800s';task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
s=json.dumps(w).replace('gpu29-train02','gpu30-sequence01').replace('gpu29/train01/job-status02.json','gpu30/sequence01/job-status.json').replace('creationTimestamp) + 1800','creationTimestamp) + 2100');(R/'workflow.yaml').write_text(yaml.safe_dump(json.loads(s),sort_keys=False))
s=(P/'launch02.py').read_text().replace('gpu29-train02','gpu30-sequence01').replace("'corrected_prepared'","'prepared'").replace('workflow02.yaml','workflow.yaml').replace('results/execution02.json','results/execution.json');(R/'launch.py').write_text(s)
s=(P/'collect02.py').read_text().replace('gpu29-train02','gpu30-sequence01').replace('results/execution02.json','results/execution.json').replace('gpu29/train01/','gpu30/sequence01/').replace("'/inputs.tar'","'/overlay.tar'").replace('data/train01','data/cloud');s=s.replace(" if (R/'data/cloud/complete.json').exists():subprocess.run([__import__('sys').executable,str(R/'ingest.py')],check=True)\n",'');(R/'collect.py').write_text(s)
if not (R/'budget.json').exists():(R/'budget.json').write_text(json.dumps(dict(cap_usd=1,reserved_usd=1,state='prepared',reserved_unix=time.time(),queue_limit_s=1200,vm_age_limit_s=2100,absolute_limit_s=3300,compute_envelope_rate_usd_hour=.8,ancillary_allowance_usd=1-.8*3300/3600,retries=0),indent=2))
print('Prepared bounded sequence job')
