"""Bounded phase submission; reserve full timeout cost, no retries or recycling."""
import base64,lzma,fcntl,hashlib,json,subprocess,time,tarfile
from pathlib import Path
import yaml
ROOT=Path(__file__).parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';PROJECT='tmrw-wildfire-20261015'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],text=True,capture_output=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def read(p):return json.loads((ROOT/p).read_text())
def save(p,obj):(ROOT/p).write_text(json.dumps(obj,indent=2)+'\n')
def verify():
 f=read('results/input-freeze.json');assert hashlib.sha256((ROOT/'data/tree-templates.json').read_bytes()).hexdigest()==f['template_sha256']
 for name,h in f['cases'].items():assert hashlib.sha256((ROOT/'decks'/f'{name}.fds').read_bytes()).hexdigest()==h

def prepare():
 verify();assert not (ROOT/'budget.json').exists()
 cases=read('cases.json');cal=[c for c in cases if c['family']=='single' and c['case'].endswith('_1')];dev=[c for c in cases if c['split'] in ['train','validation'] and c not in cal];test=[c for c in cases if c['split'].endswith('test')];groups=[]
 for phase,rows in [('calibration',cal),('development',dev),('test',test)]:
  for i in range(0,len(rows),3):
   cs=rows[i:i+3];name=f't26-{phase}-{i//3}';g=dict(id=name,phase=phase,cases=[c['case'] for c in cs],duration_s=5400,allowance_usd=.20)
   runner=(ROOT/'runner-template.py').read_text().replace('overnight21/overnight21_stronger/',f'transfer26/{name}/').replace('400*1024**2','500*1024**2').replace('timeout=90','timeout=300')
   payload={'runner.py':runner,'worker.py':(ROOT/'worker.py').read_text(),'cases.json':json.dumps(cs),'group.json':json.dumps(g)}
   payload['build.py']=(ROOT/'build.py').read_text();payload['base-input.fds']=(ROOT/'base-input.fds').read_text()
   payload['reference-particles.json']=json.dumps({k:v[:400] for k,v in read('reference-particles.json').items()})
   payload['input-freeze.json']=json.dumps(read('results/input-freeze.json'))
   encoded=base64.b64encode(lzma.compress(json.dumps(payload).encode(),preset=9)).decode()
   bootstrap="import json,lzma,base64,pathlib,sys,runpy; root=pathlib.Path('/study'); payload=json.loads(lzma.decompress(base64.b64decode("+repr(encoded)+"))); [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_text(v) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
   w=read('workflow-template.json');ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + 5280}';job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']='5160s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
   job['labels']['trial_id']=name;job['allocationPolicy']['labels']['trial_id']=name
   raw=json.dumps(w).replace('fds-controlled-trial','fds-'+name).replace('domain17/job-status.json',f'transfer26/{name}/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+name)
   folder=ROOT/'jobs'/name;folder.mkdir(exist_ok=True);(folder/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));save(f'jobs/{name}/group.json',g);groups.append(g)
 save('groups.json',groups);assert sum(g['allowance_usd'] for g in groups)<2.20001
 print('Prepared',len(groups),'groups; total timeout allowance',round(sum(g['allowance_usd'] for g in groups),2))

def launch(name,cap):
 verify();g=next(g for g in read('groups.json') if g['id']==name)
 checks=read('results/preflight.json');assert len(checks)==11 and all(x['passed'] for x in checks)
 if g['phase']=='development':
  decision=read('results/calibration-decision.json');assert decision['release_development'] is True
  cs=[c for c in read('cases.json') if c['case'] in g['cases']]
  assert all(t['type'] in decision['allowed_types'] for c in cs for t in c['trees']), 'Type calibration not reviewed'
 if g['phase']=='test':
  freeze=read('results/prediction-freeze.json')
  for filename,h in freeze['files'].items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==h
  assert all(c in freeze['cases'] for c in g['cases'])
 with (ROOT/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  ledger=read('budget.json') if (ROOT/'budget.json').exists() else dict(authorized_usd=cap,reserved_usd=0,reservations={},rate_assumption_usd_per_vm_hour=.08,automatic_retries=False,recycle_reservations=False)
  assert cap==ledger['authorized_usd'] and name not in ledger['reservations']
  assert ledger['reserved_usd']+g['allowance_usd']<=cap+1e-8
  # Existing resources must all belong to this experiment; max six VMs.
  vms=gc('compute','instances','list');jobs=gc('batch','jobs','list','--location=us-central1')
  assert len(vms)<6 and len(jobs)<6
  assert all(x.get('labels',{}).get('trial_id','').startswith('t26-') for x in vms+jobs)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];file=ROOT/'jobs'/name/'workflow.yaml'
  gc('workflows','deploy','fds-'+name,'--location=us-central1','--source='+str(file),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe','fds-'+name,'--location=us-central1')['sourceContents'])==yaml.safe_load(file.read_text())
  ledger['reserved_usd']=round(ledger['reserved_usd']+g['allowance_usd'],4);ledger['reservations'][name]=dict(g,state='reserved',reserved_unix=time.time());save('budget.json',ledger)
  result=gc('workflows','execute','fds-'+name,'--location=us-central1');save(f'jobs/{name}/execution.json',result);ledger['reservations'][name].update(state='submitted',execution=result['name']);save('budget.json',ledger);print('SUBMITTED',name,flush=True)

def collect(name):
 g=next(g for g in read('groups.json') if g['id']==name);folder=ROOT/'jobs'/name
 e=json.loads((folder/'execution.json').read_text())['name'].split('/');st=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');save(f'jobs/{name}/status.json',st)
 if st['state']=='ACTIVE':return dict(group=name,state='ACTIVE')
 inventory={k:gc(*a,'--filter=labels.trial_id='+name) for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};save(f'jobs/{name}/cleanup.json',inventory);assert not any(inventory.values()),'Cleanup incomplete'
 rows=[]
 for cname in g['cases']:
  archive=ROOT/'data/downloads'/(cname+'.tar.gz');dest=ROOT/'data/cloud'/cname
  if not archive.exists():
   p=subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/transfer26/{name}/{cname}.tar.gz',str(archive)],capture_output=True,text=True,timeout=240)
   if p.returncode:return dict(group=name,state=st['state'],collection_error=p.stderr)
  if not (dest/'result.json').exists():
   with tarfile.open(archive) as t:t.extractall(dest.parent,filter='data')
  assert hashlib.sha256((dest/(cname+'.fds')).read_bytes()).hexdigest()==read('results/input-freeze.json')['cases'][cname]
  for r in json.loads((dest/'checkpoint-manifest.json').read_text())['files']:assert hashlib.sha256((dest/r['name']).read_bytes()).hexdigest()==r['sha256']
  assert json.loads((dest/'linux-resume-preflight.json').read_text())['passed'];rows.append(json.loads((dest/'result.json').read_text()))
 with (ROOT/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);ledger=read('budget.json');ledger['reservations'][name]['state']='terminal_cleanup_verified';save('budget.json',ledger)
 result=dict(group=name,state=st['state'],collected=len(rows),all_full_horizon=all(r['full_horizon'] for r in rows));save(f'jobs/{name}/completion.json',result);return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch','collect']);p.add_argument('--group');p.add_argument('--cap',type=float,default=1.);a=p.parse_args()
 if a.action=='prepare':prepare()
 elif a.action=='launch':launch(a.group,a.cap)
 else:print(json.dumps(collect(a.group)),flush=True)
