"""Prepare/check/launch one explicitly authorized sampling isolation case."""
import base64,csv,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
import numpy as np,yaml
from scene import ROOT
from control import gc,G
NAME='sampling21_dense';JOB=ROOT/'jobs'/NAME;LEDGER=ROOT/'budget-sampling.json'
BINARY=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
def prepare():
 JOB.mkdir(exist_ok=True)
 source=(ROOT/'inputs/corrective_candidates/candidate_coarse_dense_particles.fds').read_text().replace("CHID='candidate_coarse_dense_particles'",f"CHID='{NAME}'").replace('DT_RESTART=100000.','DT_RESTART=10.')
 # Spatially disjoint per-crown channels, so one burning crown cannot mask another.
 from scene import CLASSES
 extra=''
 for tag,box in [('small','0,24,0,14.99,0,24'),('large','0,24,15,24,0,24')]:
  for fuel,_ in CLASSES:
   extra+=f"&DEVC ID='{tag} mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /\n"
   extra+=f"&DEVC ID='{tag} fuel {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /\n"
 source=source.replace('&TAIL /',extra+'&TAIL /');(ROOT/'decks'/f'{NAME}.fds').write_text(source)
 metadata=dict(case=NAME,horizon_s=90,variant='passive',profile=False,deck_sha256=hashlib.sha256(source.encode()).hexdigest(),checkpoint_interval_sim_s=10,grid_m=.5,vegetation_particles_per_cell=8)
 (JOB/'case.json').write_text(json.dumps(metadata,indent=2))
 # Preserve checkpoints and input deck in the result bundle. Allow two minutes for graceful checkpoint flush.
 runner=(ROOT.parent/'20_composition_iterative/runner.py').read_text().replace("'composition19/'",repr('sampling21/'+NAME+'/')).replace('>30:', '>120:').replace("    for restart in folder.glob('*.restart'):restart.unlink()", "    (folder/(name+'.fds')).write_bytes((ROOT/'decks'/f'{name}.fds').read_bytes())\n    save(folder/'checkpoint-manifest.json', {'files': [{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.glob('*.restart')], 'binary_sha256':result['binary_sha256'], 'resume_requires':'same Linux binary, all result files and RESTART=T; no automatic resubmission'})").replace('50*1024**2','400*1024**2')
 (JOB/'runner.py').write_text(runner)
 worker="import json\nfrom pathlib import Path\nimport runner\nPath('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)\nc=json.loads(Path('/study/case.json').read_text())\nrunner.run(c,6600)\n"
 payload={'worker.py':worker,'runner.py':runner,'case.json':json.dumps(metadata),f'decks/{NAME}.fds':source};payload={k:base64.b64encode(v.encode()).decode() for k,v in payload.items()}
 bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
 w=json.loads((ROOT.parent/'20_composition_iterative/workflow_template.json').read_text());ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + 6900}';j=ass[1]['job'];task=j['taskGroups'][0]['taskSpec'];task['maxRunDuration']='6780s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
 label=NAME.replace('_','-');j['labels']['trial_id']=label;j['allocationPolicy']['labels']['trial_id']=label
 raw=json.dumps(w).replace('fds-controlled-trial','fds-'+label).replace('domain17/job-status.json','sampling21/'+NAME+'/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+label)
 (JOB/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False))
 print('Prepared',NAME,flush=True)
def preflight():
 w=ROOT/'data/sampling_preflight';w.mkdir(exist_ok=True);s=(ROOT/'decks'/f'{NAME}.fds').read_text().replace('T_END=90','T_END=1.05').replace('DT_RESTART=10.','DT_RESTART=.5')
 env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0')
 def solve(text,label):
  (w/'check.fds').write_text(text)
  with (w/(label+'.log')).open('w') as f:p=subprocess.run([str(BINARY),'check.fds'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
  assert p.returncode==0 and 'completed successfully' in (w/(label+'.log')).read_text().lower(),label
 solve(s,'initial');checkpoints=list(w.glob('*.restart'));assert checkpoints
 before=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in checkpoints]
 # Same case and files, longer end time; verifies FDS reads a real saved checkpoint.
 resumed=s.replace('T_END=1.05','T_END=1.55').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,')
 assert 'RESTART=T' in resumed;solve(resumed,'resumed')
 with (w/(NAME+'_devc.csv')).open() as f:
  it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];a=np.array([list(map(float,row)) for row in it]);d=dict(zip(keys,a.T))
 assert d['Time'][-1]>=1.55-1e-5 and np.isfinite(a).all()
 mass=sum(v for k,v in d.items() if k.startswith('mass '));small=sum(v for k,v in d.items() if k.startswith('small mass '));large=sum(v for k,v in d.items() if k.startswith('large mass '));assert max(abs(mass-small-large))<1e-4
 report=dict(passed=True,restart_exercised=True,last_time_s=float(d['Time'][-1]),checkpoints_before_resume=before,mass_partition_max_error_kg=float(max(abs(mass-small-large))),scope='Native macOS checkpoint/resume and deck startup. Linux checkpoint binary must be resumed using matching Linux build, not this native binary.')
 (ROOT/'results/sampling-preflight.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
def launch():
 assert json.loads((ROOT/'results/sampling-price.json').read_text())['usd_per_vm_hour'] <= .08
 assert json.loads((ROOT/'results/sampling-preflight.json').read_text())['passed']
 with (ROOT/'data/sampling-budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);assert not LEDGER.exists(),'Never repeat an existing reservation'
  assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1')
  for w in gc('workflows','list','--location=us-central1'):assert not gc('workflows','executions','list',w['name'].split('/')[-1],'--location=us-central1','--filter=state=ACTIVE')
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];wf='fds-'+NAME.replace('_','-');f=JOB/'workflow.yaml'
  gc('workflows','deploy',wf,'--location=us-central1','--source='+str(f),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',wf,'--location=us-central1')['sourceContents'])==yaml.safe_load(f.read_text())
  ledger=dict(authorized_usd=.25,reserved_usd=.25,vm_hours=2,rate_ceiling=.08,ancillary_allowance=.09,state='reserved',automatic_retries=False,scope='User run it for particle-density isolation only',reserved_unix=time.time(),case=json.loads((JOB/'case.json').read_text()))
  LEDGER.write_text(json.dumps(ledger,indent=2));r=gc('workflows','execute',wf,'--location=us-central1');(JOB/'execution.json').write_text(json.dumps(r,indent=2));ledger.update(state='submitted',execution=r['name']);LEDGER.write_text(json.dumps(ledger,indent=2));print('SUBMITTED',r['name'],flush=True)
if __name__=='__main__':
 import sys
 {'prepare':prepare,'preflight':preflight,'launch':launch}[sys.argv[1]]()
