"""Explicitly budgeted Stage A per-case workflows; no implicit retries."""
import argparse,base64,fcntl,hashlib,json,subprocess,tarfile,time
from pathlib import Path
import yaml
from scene import ROOT,deck
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';PROJECT='tmrw-wildfire-20261015'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],text=True,capture_output=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def prepare(records,wave):
 template=json.loads((ROOT.parent/'20_composition_iterative/workflow_template.json').read_text())
 runner=(ROOT.parent/'20_composition_iterative/runner.py').read_text()
 for r in records:
  name=r['case'];folder=ROOT/'jobs'/name;folder.mkdir(parents=True,exist_ok=True)
  s,metadata=deck(r);(ROOT/'decks'/f'{name}.fds').write_text(s)
  worker="""import json\nfrom pathlib import Path\nimport runner\nPath('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)\nc=json.loads(Path('/study/case.json').read_text())\nr=runner.run(c,CASE_LIMIT)\nif not r['full_horizon']:raise RuntimeError('Incomplete case; no retry')\n""".replace('CASE_LIMIT',str(2400 if wave==1 else 6000))
  payload={'worker.py':worker,'runner.py':runner.replace("'composition19/'","'components21/'+"+repr(name+'/') ).replace('50*1024**2','100*1024**2'), 'case.json':json.dumps(metadata),f'decks/{name}.fds':s}
  payload={k:base64.b64encode(v.encode()).decode() for k,v in payload.items()}
  bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
  w=json.loads(json.dumps(template));steps=w['main']['steps'];assign=steps[0]['initialize']['assign'];assign[0]['deadline']='${sys.now() + '+str(3300 if wave==1 else 6900)+'}'
  job=assign[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(2700 if wave==1 else 6300)+'s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
  label='c21-'+name.replace('_','-');jobid='fds-'+label
  job['labels']['trial_id']=label;job['allocationPolicy']['labels']['trial_id']=label
  # Global substitution only on template job ID, path and cleanup label.
  raw=json.dumps(w).replace('fds-controlled-trial',jobid).replace('domain17/job-status.json','components21/'+name+'/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+label)
  w=json.loads(raw);(folder/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
  (folder/'spec.json').write_text(json.dumps(dict(case=name,wave=wave,workflow='fds-'+label,allowance_usd=.125 if wave==1 else .25,reserved_vm_hours=1 if wave==1 else 2,deck_sha256=metadata['deck_sha256']),indent=2))
 print('Prepared wave',wave,len(records))
def launch(wave):
 specs=[json.loads(p.read_text()) for p in sorted((ROOT/'jobs').glob('*/spec.json')) if json.loads(p.read_text())['wave']==wave]
 assert len(specs)==4
 with (ROOT/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);ledger=json.loads((ROOT/'budget.json').read_text())
  assert all(r['passed'] for r in json.loads((ROOT/'results/preflight.json').read_text()))
  assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1'),'Existing cloud work'
  for w in gc('workflows','list','--location=us-central1'):
   assert not gc('workflows','executions','list',w['name'].split('/')[-1],'--location=us-central1','--filter=state=ACTIVE'),'Existing controller'
  assert not any(s['case'] in {r['case'] for r in ledger['reservations']} for s in specs),'Never resubmit a reserved case'
  assert sum(r['allowance_usd'] for r in ledger['reservations'])+sum(s['allowance_usd'] for s in specs)<=1.5
  assert sum(r['reserved_vm_hours'] for r in ledger['reservations'])+sum(s['reserved_vm_hours'] for s in specs)<=12
  if wave==2:assert json.loads((ROOT/'results/wave1-gate.json').read_text())['allow_wave2']
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  for s in specs:
   f=ROOT/'jobs'/s['case']/'workflow.yaml';w=yaml.safe_load(f.read_text());j=w['main']['steps'][0]['initialize']['assign'][1]['job'];t=j['taskGroups'][0]
   assert t['taskCount']=='1' and t['taskSpec']['maxRetryCount']==0 and j['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT'
   gc('workflows','deploy',s['workflow'],'--location=us-central1','--source='+str(f),'--service-account='+sa)
   assert yaml.safe_load(gc('workflows','describe',s['workflow'],'--location=us-central1')['sourceContents'])==w
  for s in specs:ledger['reservations'].append(dict(s,state='reserved',reserved_unix=time.time()))
  (ROOT/'budget.json').write_text(json.dumps(ledger,indent=2)+'\n')
  for s in specs:
   result=gc('workflows','execute',s['workflow'],'--location=us-central1');(ROOT/'jobs'/s['case']/'execution.json').write_text(json.dumps(result,indent=2))
   next(r for r in ledger['reservations'] if r['case']==s['case']).update(state='submitted',execution=result['name']);(ROOT/'budget.json').write_text(json.dumps(ledger,indent=2)+'\n');print(s['case'],result['name'],flush=True)
def status():
 rows=[]
 for p in sorted((ROOT/'jobs').glob('*/execution.json')):
  e=json.loads(p.read_text())['name'];parts=e.split('/');s=gc('workflows','executions','describe',parts[-1],'--workflow='+parts[-3],'--location=us-central1');(p.parent/'status.json').write_text(json.dumps(s,indent=2));rows.append(dict(case=p.parent.name,state=s['state']))
 print(json.dumps(rows));return rows
def fetch():
 assert all(r['state']!='ACTIVE' for r in status())
 inventory={k:gc(*a) for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};(ROOT/'results/cleanup.json').write_text(json.dumps(inventory,indent=2));assert not any(inventory.values()),'Cloud resources remain'
 for p in sorted((ROOT/'jobs').glob('*/execution.json')):
  name=p.parent.name;dest=ROOT/'data/downloads';dest.mkdir(exist_ok=True);archive=dest/(name+'.tar.gz')
  if not archive.exists():subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/components21/{name}/{name}.tar.gz',str(archive)],check=True)
  out=ROOT/'data/cloud';out.mkdir(exist_ok=True)
  if not (out/name/'result.json').exists():
   with tarfile.open(archive) as t:t.extractall(out,filter='data')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['launch','status','fetch']);p.add_argument('wave',nargs='?',type=int);a=p.parse_args();launch(a.wave) if a.action=='launch' else globals()[a.action]()
