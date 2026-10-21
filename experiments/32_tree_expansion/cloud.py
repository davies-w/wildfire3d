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
 for name,h in f['cases'].items():assert hashlib.sha256((ROOT/'data/decks'/f'{name}.fds').read_bytes()).hexdigest()==h

def prepare():
 verify();reserved=read('budget.json')['reservations'] if (ROOT/'budget.json').exists() else {}
 cases=read('cases.json');groups=[]
 # Six development cases cover extremes plus a repeated-seed configuration.
 dev=[c for c in cases if c['split']!='test']; checks=read('results/preflight.json')['checks']
 selected=[c for c in dev if c['case'] in {x['case'] for x in checks}]
 for c in sorted(dev,key=lambda c:(-c['loading_multiplier'],-c['wind_speed'],c['angle_deg'])):
  if len(selected)>=6:break
  if c not in selected:selected.append(c)
 chunks=[('coverage',selected)]
 for phase,rows in [('development',[c for c in dev if c not in selected]),('test',[c for c in cases if c['split']=='test'])]:
  chunks.extend((phase,rows[i:i+12]) for i in range(0,len(rows),12))
 for index,(phase,cs) in enumerate(chunks):
   name=f'x32-{phase}-{index:02d}'+('-r1' if phase=='coverage' else '')
   replacements=read('replacements.json') if (ROOT/'replacements.json').exists() else {}
   name=replacements.get(name,name)
   g=dict(id=name,phase=phase,cases=[c['case'] for c in cs],duration_s=16200,allowance_usd=.40)
   if name in reserved:
    assert read(f'jobs/{name}/group.json')==g;groups.append(g);continue
   runner=(ROOT/'runner-template.py').read_text().replace('overnight21/overnight21_stronger/',f'expansion32/{name}/').replace('400*1024**2','500*1024**2').replace('timeout=90','timeout=300')
   payload={'runner.py':runner,'worker.py':(ROOT/'worker.py').read_text(),'cases.json':json.dumps(cs),'group.json':json.dumps(g)}
   for c in cs:payload['decks/'+c['case']+'.fds']=(ROOT/'data/decks'/(c['case']+'.fds')).read_text()
   freeze=read('results/input-freeze.json')
   freeze['cases']={c['case']:freeze['cases'][c['case']] for c in cs}
   payload['input-freeze.json']=json.dumps(freeze)
   encoded=base64.b64encode(lzma.compress(json.dumps(payload).encode(),preset=9)).decode()
   bootstrap="import json,lzma,base64,pathlib,sys,runpy; root=pathlib.Path('/study'); payload=json.loads(lzma.decompress(base64.b64decode("+repr(encoded)+"))); [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_text(v) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
   w=read('workflow-template.json');ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + '+'17820'+'}';job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(g['duration_s']-240)+'s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
   job['labels']['trial_id']=name;job['allocationPolicy']['labels']['trial_id']=name
   raw=json.dumps(w).replace('fds-controlled-trial','fds-'+name).replace('domain17/job-status.json',f'expansion32/{name}/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+name)
   folder=ROOT/'jobs'/name;folder.mkdir(parents=True,exist_ok=True);(folder/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));assert (folder/'workflow.yaml').stat().st_size<=128*1024, 'Workflow exceeds cloud source limit';save(f'jobs/{name}/group.json',g);groups.append(g)
 save('groups.json',groups);assert sum(g['allowance_usd'] for g in groups)<=16+1e-8
 print('Prepared',len(groups),'groups; total timeout allowance',round(sum(g['allowance_usd'] for g in groups),2))

def launch(name,cap):
 verify();g=next(g for g in read('groups.json') if g['id']==name)
 checks=read('results/preflight.json')['checks'];assert len(checks)>=4 and all(x['passed'] for x in checks)
 if g['phase']=='development':assert read('results/coverage-review.json')['passed'], 'Coverage must be reviewed before expansion'
 if g['phase']=='test':
  freeze=read('results/prediction-freeze.json')
  for filename,h in freeze['files'].items():
   if filename.endswith('.npz'):
    meta=gc('storage','objects','describe','gs://tmrw-wildfire-20261015-trial/expansion32/gpu01/predictions/'+Path(filename).name)
    assert meta.get('md5_hash',meta.get('md5Hash'))==freeze['prediction_md5'][Path(filename).name]
   else:assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==h
 with (ROOT/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  ledger=read('budget.json') if (ROOT/'budget.json').exists() else dict(authorized_usd=cap,reserved_usd=0,reservations={},rate_assumption_usd_per_vm_hour=.08,automatic_retries=False,recycle_reservations=False)
  assert cap==ledger['authorized_usd'] and name not in ledger['reservations']
  assert ledger['reserved_usd']+g['allowance_usd']<=cap+1e-8
  # Existing resources must all belong to this experiment; max six VMs.
  vms=gc('compute','instances','list');jobs=gc('batch','jobs','list','--location=us-central1')
  assert len(vms)<6 and len(jobs)<6
  assert all(x.get('labels',{}).get('trial_id','').startswith('x32-') for x in vms+jobs)
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
  uri=f'gs://tmrw-wildfire-20261015-trial/expansion32/{name}/{cname}'
  dest=ROOT/'data/summaries';dest.mkdir(parents=True,exist_ok=True);p=dest/(cname+'.json')
  if not p.exists():
   q=subprocess.run([G,'storage','cp',uri+'.summary.json',str(p)],capture_output=True,text=True,timeout=240)
   if q.returncode:return dict(group=name,state=st['state'],collection_error=q.stderr)
  summary=json.loads(p.read_text());assert summary['deck_sha256']==read('results/input-freeze.json')['cases'][cname]
  assert summary['resume']['passed'] and summary['checkpoint_manifest']['files']
  metadata=gc('storage','objects','describe',uri+'.tar.gz')
  assert int(metadata['size'])==summary['raw_bytes']
  save(f'jobs/{name}/{cname}-raw-object.json',metadata);rows.append(summary['result'])
 with (ROOT/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);ledger=read('budget.json');ledger['reservations'][name]['state']='terminal_cleanup_verified';save('budget.json',ledger)
 result=dict(group=name,state=st['state'],collected=len(rows),all_full_horizon=all(r['full_horizon'] for r in rows));save(f'jobs/{name}/completion.json',result);return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch','collect']);p.add_argument('--group');p.add_argument('--cap',type=float,default=25);a=p.parse_args()
 if a.action=='prepare':prepare()
 elif a.action=='launch':launch(a.group,a.cap)
 else:print(json.dumps(collect(a.group)),flush=True)
