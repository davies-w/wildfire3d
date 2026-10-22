import base64,lzma,fcntl,hashlib,json,subprocess,time,tarfile
from pathlib import Path
import yaml
ROOT=Path(__file__).parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';PROJECT='tmrw-wildfire-20261015'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],text=True,capture_output=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def groups():return json.loads((ROOT/'groups.json').read_text())
def prepare():
 assert not (ROOT/'budget.json').exists()
 cs=json.loads((ROOT/'cases.json').read_text());gs=[]
 template=json.loads((ROOT.parent/'20_composition_iterative/workflow_template.json').read_text())
 (ROOT/'workflow-template.json').write_text(json.dumps(template,indent=2))
 runner=(ROOT.parent/'21_local_components/jobs/overnight21_stronger/runner.py').read_text()
 (ROOT/'runner-template.py').write_text(runner)
 for layout in 'ABC':
  for dx in [1,.5]:
   name=f'p23-{layout.lower()}-{str(dx).replace(".","p")}';duration=4500 if dx==.5 else 2100
   group=dict(id=name,layout=layout,dx=dx,duration_s=duration,allowance_usd=.22 if dx==.5 else .10)
   cases=[c for c in cs if c['layout']==layout and c['dx']==dx]
   r=runner.replace('overnight21/overnight21_stronger/',f'mesh23/{name}/').replace('400*1024**2','500*1024**2').replace('timeout=90','timeout=300')
   payload={'runner.py':r,'worker.py':(ROOT/'worker.py').read_text(),'cases.json':json.dumps(cases),'group.json':json.dumps(group)}
   for c in cases:payload['decks/'+c['case']+'.fds']=(ROOT/'decks'/(c['case']+'.fds')).read_text()
   encoded=base64.b64encode(lzma.compress(json.dumps(payload).encode(),preset=9)).decode()
   bootstrap="import json,lzma,base64,pathlib,sys,runpy; root=pathlib.Path('/study'); payload=json.loads(lzma.decompress(base64.b64decode("+repr(encoded)+"))); [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_text(v) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
   w=json.loads(json.dumps(template));ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + '+str(duration-120)+'}';job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(duration-240)+'s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
   job['labels']['trial_id']=name;job['allocationPolicy']['labels']['trial_id']=name
   raw=json.dumps(w).replace('fds-controlled-trial','fds-'+name).replace('domain17/job-status.json',f'mesh23/{name}/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+name)
   folder=ROOT/'jobs'/name;folder.mkdir(exist_ok=True);(folder/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));(folder/'group.json').write_text(json.dumps(group,indent=2));gs.append(group)
 (ROOT/'groups.json').write_text(json.dumps(gs,indent=2));print('Prepared six controllers, two cases each; no submission')
def launch():
 checks=json.loads((ROOT/'results/preflight.json').read_text());assert len(checks)==12 and all(x['passed'] for x in checks)
 with (ROOT/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);assert not (ROOT/'budget.json').exists(),'Never repeat reserved launch'
  assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1')
  q=gc('compute','regions','describe','us-central1')['quotas'];(ROOT/'results/quota.json').write_text(json.dumps(q,indent=2))
  assert next(x for x in q if x['metric']=='C3_CPUS')['limit']>=24
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  for g in groups():
   file=ROOT/'jobs'/g['id']/'workflow.yaml'
   gc('workflows','deploy','fds-'+g['id'],'--location=us-central1','--source='+str(file),'--service-account='+sa)
   assert yaml.safe_load(gc('workflows','describe','fds-'+g['id'],'--location=us-central1')['sourceContents'])==yaml.safe_load(file.read_text())
  total=round(sum(g['allowance_usd'] for g in groups()),6);assert total<=1
  ledger=dict(authorized_usd=1,reserved_usd=total,compute_rate_assumption=.08,reservations={g['id']:dict(g,state='reserved',reserved_unix=time.time()) for g in groups()},automatic_retries=False,recycle_reservations=False)
  (ROOT/'budget.json').write_text(json.dumps(ledger,indent=2))
  for g in groups():
   result=gc('workflows','execute','fds-'+g['id'],'--location=us-central1');(ROOT/'jobs'/g['id']/'execution.json').write_text(json.dumps(result,indent=2));ledger['reservations'][g['id']].update(state='submitted',execution=result['name']);(ROOT/'budget.json').write_text(json.dumps(ledger,indent=2));print('SUBMITTED',g['id'],flush=True)
def collect():
 rows=[]
 for g in groups():
  folder=ROOT/'jobs'/g['id'];ep=folder/'execution.json'
  if not ep.exists():continue
  e=json.loads(ep.read_text())['name'].split('/');st=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');(folder/'status.json').write_text(json.dumps(st,indent=2));rows.append(dict(group=g['id'],state=st['state']))
  if st['state']=='ACTIVE':continue
  inventory={k:gc(*a,'--filter=labels.trial_id='+g['id']) for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
  (folder/'cleanup.json').write_text(json.dumps(inventory,indent=2));assert not any(inventory.values()),'Cleanup incomplete'
  for c in json.loads((ROOT/'cases.json').read_text()):
   if c['layout']!=g['layout'] or c['dx']!=g['dx']:continue
   name=c['case'];archive=ROOT/'data/downloads'/(name+'.tar.gz');dest=ROOT/'data/cloud'/name
   if not archive.exists():
    p=subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/mesh23/{g["id"]}/{name}.tar.gz',str(archive)],capture_output=True,text=True)
    if p.returncode:rows[-1]['collection_error']=p.stderr;continue
   if not (dest/'result.json').exists():
    with tarfile.open(archive) as t:t.extractall(dest.parent,filter='data')
   assert hashlib.sha256((dest/(name+'.fds')).read_bytes()).hexdigest()==c['deck_sha256']
   for r in json.loads((dest/'checkpoint-manifest.json').read_text())['files']:assert hashlib.sha256((dest/r['name']).read_bytes()).hexdigest()==r['sha256']
   assert json.loads((dest/'linux-resume-preflight.json').read_text())['passed']
  ledger=json.loads((ROOT/'budget.json').read_text());ledger['reservations'][g['id']]['state']='terminal_cleanup_verified';(ROOT/'budget.json').write_text(json.dumps(ledger,indent=2))
 (ROOT/'results/status.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows),flush=True);return rows
if __name__=='__main__':
 import sys
 {'prepare':prepare,'launch':launch,'collect':collect}[sys.argv[1]]()
