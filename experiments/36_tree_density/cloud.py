"""Bounded, centrally reserved campaign; immutable outputs and no automatic paid retries."""
from pathlib import Path
import json,subprocess,hashlib,fcntl,time,datetime,base64,lzma,copy,yaml
R=Path(__file__).resolve().parent;ROOT=R;G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud');PROJECT='tmrw-wildfire-20261015';BUCKET=PROJECT+'-trial';B=R.parent/'33_representation_loss/budget.json'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],text=True,capture_output=True,timeout=240)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def read(p):return json.loads((R/p).read_text())
def save(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n')
def prepare():
 assert not (R/'results/reserved.json').exists(),'Campaign frozen after reservation'
 assert read('results/preflight.json')['passed']
 cases=read('cases.json');wanted=read('results/design.json')['coverage_cases'];coverage=[c for c in cases if c['case'] in wanted];remaining=[c for c in cases if c['case'] not in wanted];chunks=[('coverage',coverage)]+[('density',remaining[i:i+12]) for i in range(0,len(remaining),12)];groups=[]
 for i,(phase,cs) in enumerate(chunks):
  name=f'x36-{phase}-{i:03d}';g=dict(id=name,phase=phase,cases=[c['case'] for c in cs],duration_s=16200,allowance_usd=.4);folder=R/'jobs'/name;folder.mkdir(exist_ok=True)
  payload={'runner.py':(R/'runner-template.py').read_text(),'worker.py':(R/'worker.py').read_text(),'transport.py':(R/'transport.py').read_text(),'cases.json':json.dumps(cs),'group.json':json.dumps(g),'input-freeze.json':json.dumps(dict(cases={c['case']:c['deck_sha256'] for c in cs}))}
  for c in cs:payload['decks/'+c['case']+'.fds']=(R/'data/decks'/(c['case']+'.fds')).read_text()
  blob=lzma.compress(json.dumps(payload).encode(),preset=6);bp=R/'data/packages'/(name+'.xz');bp.parent.mkdir(exist_ok=True);bp.write_bytes(blob);g['package_sha256']=hashlib.sha256(blob).hexdigest()
  bootstrap="import json,lzma,pathlib,sys,runpy,urllib.request,hashlib;req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});tok=json.load(urllib.request.urlopen(req,timeout=30))['access_token'];req=urllib.request.Request('https://storage.googleapis.com/"+BUCKET+"/density36/"+name+"/input.xz',headers={'Authorization':'Bearer '+tok});blob=urllib.request.urlopen(req,timeout=120).read();assert hashlib.sha256(blob).hexdigest()=="+repr(g['package_sha256'])+";root=pathlib.Path('/study');payload=json.loads(lzma.decompress(blob));[(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload];[(root/n).write_text(v) for n,v in payload.items()];sys.path.insert(0,'/study');runpy.run_path('/study/worker.py',run_name='__main__')"
  w=read('workflow-template.json');ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + 17820}';ass.append({'queue_deadline':'${sys.now() + 1200}'});job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']='15960s';task['runnables'][0]['container']['commands']=['-c',bootstrap];job['labels']['trial_id']=name;job['allocationPolicy']['labels']['trial_id']=name
  w['main']['steps'][2]['monitor']['try']['steps'][1]['check']['switch'].append(dict(condition='${(status.body.status.state == "QUEUED" or status.body.status.state == "SCHEDULED") and sys.now() >= queue_deadline}',next='record'))
  raw=json.dumps(w).replace('fds-controlled-trial','fds-'+name).replace('domain17/job-status.json',f'density36/{name}/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+name)
  p=folder/'workflow.yaml';p.write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));assert p.stat().st_size<128*1024
  g['workflow_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();save(f'jobs/{name}/group.json',g);groups.append(g)
 save('groups.json',groups);assert len(groups)==131 and sum(len(g['cases']) for g in groups)==1560
 print('Prepared131boundedgroups',flush=True)
def reserve():
 with (B.parent/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());groups=read('groups.json');assert not any(g['id'] in b['reservations'] for g in groups)
  total=round(sum(g['allowance_usd'] for g in groups)+18,2);assert total==70.4;assert b['estimated_spend_usd']+b['reserved_usd']+total<=b['authorized_usd']
  for g in groups:b['reservations'][g['id']]=dict(state='reserved_before_upload',allowance_usd=g['allowance_usd'],reserved_unix=time.time(),scope='CPU group maximum lifetime at .08USD/h',cases=len(g['cases']))
  for key,value in [('density36-storage',10),('density36-learning',8)]:b['reservations'][key]=dict(state='reserved_before_upload',allowance_usd=value,reserved_unix=time.time(),scope='Campaign ancillary/storage' if value==10 else 'Later unchanged-model grouped ten-fold evaluation; hyperparameter trials not launched')
  b['reserved_usd']=round(b['reserved_usd']+total,2);B.write_text(json.dumps(b,indent=2)+'\n');save('results/reserved.json',dict(total_allowance_usd=total,pre_run_estimate_usd=b['estimated_spend_usd'],cap_usd=b['authorized_usd']))
def launch(name):
 g=next(g for g in read('groups.json') if g['id']==name);folder=R/'jobs'/name
 assert read('results/preflight.json')['passed'] and read('results/workflow-preflight.json')['passed'] and read('results/transport-preflight.json')['passed']
 if g['phase']!='coverage':assert read('results/coverage-review.json')['passed']
 assert hashlib.sha256((folder/'workflow.yaml').read_bytes()).hexdigest()==g['workflow_sha256']
 with (B.parent/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());entry=b['reservations'][name];assert entry['state']=='reserved_before_upload' and not (folder/'execution.json').exists()
  vms=gc('compute','instances','list');jobs=gc('batch','jobs','list','--location=us-central1');assert len(vms)<24 and len(jobs)<24;assert all(x.get('labels',{}).get('trial_id','').startswith('x36-') for x in vms+jobs)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ');condition=dict(title=name+'-read',description='Read only this immutable output prefix for upload verification',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+'/objects/density36/'+name+"/')")
  if (folder/'read-condition.json').exists():condition=read(f'jobs/{name}/read-condition.json')
  else:save(f'jobs/{name}/read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(folder/'read-condition.json')],check=True,capture_output=True)
  package=R/'data/packages'/(name+'.xz');assert hashlib.sha256(package.read_bytes()).hexdigest()==g['package_sha256']
  uri='gs://'+BUCKET+'/density36/'+name+'/input.xz'
  if not (folder/'input-upload.json').exists():
   probe=subprocess.run([G,'storage','objects','describe',uri,'--format=json'],capture_output=True,text=True)
   if probe.returncode:
    assert '404' in probe.stderr or 'not found' in probe.stderr.lower(),probe.stderr
    subprocess.run([G,'storage','cp',str(package),uri,'--if-generation-match=0'],check=True,capture_output=True,timeout=240)
  meta=gc('storage','objects','describe',uri);assert meta['md5_hash']==base64.b64encode(hashlib.md5(package.read_bytes()).digest()).decode();save(f'jobs/{name}/input-upload.json',meta)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];gc('workflows','deploy','fds-'+name,'--location=us-central1','--source='+str(folder/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-'+name,'--location=us-central1')['sourceContents'])==yaml.safe_load((folder/'workflow.yaml').read_text())
  assert not gc('workflows','executions','list','fds-'+name,'--location=us-central1')
  entry['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
  e=gc('workflows','execute','fds-'+name,'--location=us-central1');save(f'jobs/{name}/execution.json',e);entry.update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n');print('SUBMITTED',name,e['name'],flush=True)
def collect(name):
 g=next(g for g in read('groups.json') if g['id']==name);folder=R/'jobs'/name;e=read(f'jobs/{name}/execution.json')['name'].split('/');st=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');save(f'jobs/{name}/status.json',st)
 if st['state']=='ACTIVE':return False
 inv={k:gc(*args,'--filter=labels.trial_id='+name) for k,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};save(f'jobs/{name}/cleanup.json',inv);assert not any(inv.values())
 if not (folder/'permission-removed.json').exists():
  subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(folder/'read-condition.json')],check=True,capture_output=True);save(f'jobs/{name}/permission-removed.json',dict(removed=True))
 rows=[];(R/'data/summaries').mkdir(exist_ok=True)
 for n in g['cases']:
  uri='gs://'+BUCKET+'/density36/'+name+'/'+n;p=R/'data/summaries'/(n+'.json')
  if not p.exists():subprocess.run([G,'storage','cp',uri+'.summary.json',str(p)],check=True,capture_output=True,timeout=240)
  s=json.loads(p.read_text());assert s['deck_sha256']==read('results/input-freeze.json')['cases'][n] and s['resume']['passed'] and s['checkpoint_manifest']['files']
  m=gc('storage','objects','describe',uri+'.tar.gz');assert int(m['size'])==s['raw_bytes'];save(f'jobs/{name}/{n}-raw-object.json',m);assert s['result']['full_horizon'];rows.append(s['result'])
 save(f'jobs/{name}/completion.json',dict(all_full_horizon=True,collected=len(rows),workflow_state=st['state'],cleanup_verified=True));print('COLLECTED',name,flush=True);return True
if __name__=='__main__':
 import sys
 {'prepare':prepare,'reserve':reserve}[sys.argv[1]]()
