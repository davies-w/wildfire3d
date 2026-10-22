"""Bounded matched-grid campaign. Preparing does not submit; launch reserves before execution."""
import base64,fcntl,hashlib,json,subprocess,time,tarfile
from pathlib import Path
import yaml
from scene import ROOT
from control import gc,G
LEDGER=ROOT/'budget-overnight.json'
def cases():return json.loads((ROOT/'results/overnight-grid-v2-candidates.json').read_text())['cases']

def prepare():
 for c in cases():
  name=c['case'];job=ROOT/'jobs'/name;job.mkdir(exist_ok=True)
  source=(ROOT/c['path']).read_text();assert hashlib.sha256(source.encode()).hexdigest()==c['sha256']
  (ROOT/'decks'/f'{name}.fds').write_text(source)
  meta=dict(case=name,horizon_s=40,variant='passive',profile=False,deck_sha256=c['sha256'])
  runner=(ROOT/'jobs/overnight21_stronger/runner.py').read_text().replace('overnight21/overnight21_stronger/','overnight21/'+name+'/').replace('400*1024**2','2*1024**3').replace('urlopen(req,timeout=90)','urlopen(req,timeout=600)')
  (job/'runner.py').write_text(runner)
  # Tiny-duration run on the actual mesh and binary, then resume the saved checkpoint.
  # Main case is a new directory, never continued from this preflight.
  worker='''import csv,hashlib,json,os,subprocess\nfrom pathlib import Path\nimport runner\nroot=Path('/study');c=json.loads((root/'case.json').read_text());name=c['case'];w=root/'linux_resume';w.mkdir();s=(root/'decks'/f'{name}.fds').read_text().replace('T_END=40','T_END=.1').replace('DT_RESTART=10.','DT_RESTART=.05').replace('DT_DEVC=.5','DT_DEVC=.01')\nenv=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')\ndef solve(s,label):\n (w/'check.fds').write_text(s)\n with (w/(label+'.log')).open('w') as f:p=subprocess.run([runner.BINARY,str(w/'check.fds')],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)\n assert p.returncode==0 and 'completed successfully' in (w/(label+'.log')).read_text().lower()\nsolve(s,'initial');checkpoints=list(w.glob('*.restart'));assert checkpoints\ncheckpoint_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in checkpoints}\nsolve(s.replace('T_END=.1','T_END=.15').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,'),'resumed')\nwith (w/(name+'_devc.csv')).open() as f:\n rows=list(csv.reader(f));last=float(rows[-1][0]);assert last>=.15-1e-6\nfolder=root/'data'/name;folder.mkdir(parents=True);(folder/'linux-resume-preflight.json').write_text(json.dumps(dict(passed=True,last_time=last,initial_checkpoint_hashes=checkpoint_hashes,binary_sha256=hashlib.sha256(Path(runner.BINARY).read_bytes()).hexdigest())))\nPath('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)\nrunner.run(c,LIMIT)\n'''.replace('LIMIT',str(int(c['max_vm_hours']*3600)-1800))
  # Preserve diagnostic files on preflight failure as well as normal completion.
  prefix,body=worker.split("root=Path('/study')",1)
  worker=prefix+"import traceback,tarfile\ntry:\n"+'\n'.join(' '+line for line in ("root=Path('/study')"+body).splitlines())+"\nexcept Exception:\n traceback.print_exc()\n failure=Path('/tmp')/("+repr(name)+"+'-worker-failure.tar.gz')\n with tarfile.open(failure,'w:gz') as archive:archive.add(Path('/study/linux_resume'),arcname='linux_resume')\n runner.upload(failure,failure.name)\n raise SystemExit(1)\n"
  payload={'worker.py':worker,'runner.py':runner,'case.json':json.dumps(meta),f'decks/{name}.fds':source};payload={k:base64.b64encode(v.encode()).decode() for k,v in payload.items()}
  bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
  w=json.loads((ROOT.parent/'20_composition_iterative/workflow_template.json').read_text());ass=w['main']['steps'][0]['initialize']['assign'];duration=int(c['max_vm_hours']*3600);ass[0]['deadline']='${sys.now() + '+str(duration-300)+'}';j=ass[1]['job'];task=j['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(duration-600)+'s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
  label=name.replace('_','-');j['labels']['trial_id']=label;j['allocationPolicy']['labels']['trial_id']=label
  raw=json.dumps(w).replace('fds-controlled-trial','fds-'+label).replace('domain17/job-status.json','overnight21/'+name+'/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+label)
  (job/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));(job/'case.json').write_text(json.dumps(meta,indent=2));(job/'worker.py').write_text(worker);compile(worker,'worker.py','exec')
 print('Prepared cloud workflows; not submitted')

def launch():
 assert (ROOT/'results/overnight-stronger-result.json').exists(),'Interpret stronger result first'
 assert json.loads((ROOT/'results/overnight-next-decision.json').read_text())['run_matched_grid_diagnostics'] is True, 'Persist scientific decision first'
 assert json.loads((ROOT/'results/sampling-price.json').read_text())['usd_per_vm_hour']<=.08
 assert len(json.loads((ROOT/'results/overnight-grid-v2-worker-preflight.json').read_text()))==3
 assert all(c['passed'] for c in json.loads((ROOT/'results/overnight-grid-v2-worker-preflight.json').read_text()))
 with (ROOT/'data/overnight-budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);ledger=json.loads(LEDGER.read_text());cs=cases()
  assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1'),'Existing resources must finish first'
  assert time.time()+max(c['max_vm_hours'] for c in cs)*3600+120 <= ledger['end_unix']
  assert all(c['case'] not in ledger['reservations'] for c in cs)
  assert ledger['reserved_usd']+sum(c['allowance_usd'] for c in cs)<=ledger['authorized_usd']
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  for c in cs:
   name=c['case'];job=ROOT/'jobs'/name;wf='fds-'+name.replace('_','-');f=job/'workflow.yaml'
   gc('workflows','deploy',wf,'--location=us-central1','--source='+str(f),'--service-account='+sa)
   assert yaml.safe_load(gc('workflows','describe',wf,'--location=us-central1')['sourceContents'])==yaml.safe_load(f.read_text())
  assert time.time()+max(c['max_vm_hours'] for c in cs)*3600+120 <= ledger['end_unix']
  for c in cs:
   ledger['reservations'][c['case']]=dict(allowance_usd=c['allowance_usd'],vm_hours=c['max_vm_hours'],state='reserved',reserved_unix=time.time(),case=c)
  ledger['reserved_usd']=round(ledger['reserved_usd']+sum(c['allowance_usd'] for c in cs),6);LEDGER.write_text(json.dumps(ledger,indent=2))
  for c in cs:
   name=c['case'];r=gc('workflows','execute','fds-'+name.replace('_','-'),'--location=us-central1');(ROOT/'jobs'/name/'execution.json').write_text(json.dumps(r,indent=2));ledger['reservations'][name].update(state='submitted',execution=r['name']);LEDGER.write_text(json.dumps(ledger,indent=2));print('SUBMITTED',name,flush=True)

def collect():
 for c in cases():
  name=c['case'];job=ROOT/'jobs'/name
  if not (job/'execution.json').exists():continue
  e=json.loads((job/'execution.json').read_text())['name'].split('/');status=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');(job/'status.json').write_text(json.dumps(status,indent=2))
  if status['state']=='ACTIVE':continue
  label=name.replace('_','-');inventory={k:gc(*a,'--filter=labels.trial_id='+label) for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
  assert not any(inventory.values()),'Own resources remain'
  outcome=json.loads(status.get('result','{}'))
  if outcome.get('final_state')!='SUCCEEDED':
   (ROOT/'results'/(name+'-failure.json')).write_text(json.dumps(dict(controller=status,cleanup=inventory),indent=2))
   failure=ROOT/'data/downloads'/(name+'-worker-failure.tar.gz')
   if not failure.exists():subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/overnight21/{name}/{name}-worker-failure.tar.gz',str(failure)],check=False)
   print('FAILED',name,flush=True);continue
  archive=ROOT/'data/downloads'/(name+'.tar.gz');dest=ROOT/'data/cloud'/name
  if not archive.exists():subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/overnight21/{name}/{name}.tar.gz',str(archive)],check=True)
  if not (dest/'result.json').exists():
   with tarfile.open(archive) as t:t.extractall(dest.parent,filter='data')
  manifest=json.loads((dest/'checkpoint-manifest.json').read_text())
  for f in manifest['files']:assert hashlib.sha256((dest/f['name']).read_bytes()).hexdigest()==f['sha256']
  assert json.loads((dest/'linux-resume-preflight.json').read_text())['passed']
  (ROOT/'results'/(name+'-collected.json')).write_text(json.dumps(dict(cleanup=inventory,checkpoint_files_verified=len(manifest['files']),result=json.loads((dest/'result.json').read_text())),indent=2));print('COLLECTED',name)
if __name__=='__main__':
 import sys
 {'prepare':prepare,'launch':launch,'collect':collect}[sys.argv[1]]()
