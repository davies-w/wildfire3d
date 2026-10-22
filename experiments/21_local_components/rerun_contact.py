"""Eight corrected Stage A cases; six cloud controllers with two sequential queues."""
import base64,csv,fcntl,hashlib,json,os,re,subprocess,time
from pathlib import Path
import yaml
from scene import ROOT,deck,CLASSES
from control import gc,G,PROJECT
PLAN=ROOT/'contact-stage-a.json';BUDGET=ROOT/'budget-contact-stage-a.json'
BINARY=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'

def cases():
 out=[]
 for kind in ['single','double','corner','bare']:
  out.append(dict(case='ac21_'+kind,kind=kind,direction=225 if kind=='corner' else 270,hours=.75))
 for kind in ['single','double','corner']:
  out.append(dict(case='ac21_'+kind+'_expanded',kind=kind,direction=225 if kind=='corner' else 270,expanded=True,hours=1))
 out.append(dict(case='ac21_double_fine',kind='double',direction=270,dx=.25,hours=6))
 return out

def make(c,horizon=180):
 s,r=deck(c,horizon)
 s=re.sub(r"&VENT[^\n]*SURF_ID='IGNITOR' /",'',s)
 s=s.replace('SAMPLING_FACTOR=10','SAMPLING_FACTOR=1').replace('DT_PART=5.','DT_PART=1.')
 extra="""
! Artificial crown-contact initialization; no ground-fire or ember representation.
&PART ID='contact ignitor', SAMPLING_FACTOR=1, SURF_ID='contact burner', STATIC=T, AGE=21., QUANTITIES='PARTICLE TEMPERATURE' /
&SURF ID='contact burner', TMP_FRONT=1500., EMISSIVITY=1., HRRPUA=60., RAMP_T='contact', RAMP_Q='contact', RADIUS=.01, GEOMETRY='SPHERICAL' /
&RAMP ID='contact', T=0., F=0. /
&RAMP ID='contact', T=.1, F=1. /
&RAMP ID='contact', T=20., F=1. /
&RAMP ID='contact', T=20.1, F=0. /
"""
 crowns=r['canopy_patches'] or [(11,12,3,7,2)]
 for x,y,z,h,rad in crowns:
  extra+=f"&INIT PART_ID='contact ignitor', XYZ={x},{y},{z+.1}, RADIUS={rad*.75}, SHAPE='RING', N_PARTICLES=1600 /\n"
 for fuel,_ in CLASSES:
  extra+=f"&DEVC ID='fuel_release {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={','.join(map(str,r['domain_m']))}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /\n"
 s=s.replace('&TAIL /',extra+'&TAIL /')
 r.update(source_kw=1600*4*3.141592653589793*.01**2*60*len(crowns),source_energy_kj=None,source_note='Prescribed1500 C contact heating PLUS nominal chemical HRR; removed21 s. Both double-case crowns deliberately initialized.',deck_sha256=hashlib.sha256(s.encode()).hexdigest())
 return s,r

def prepare():
 assert json.loads((ROOT/'results/contact-ignition.json').read_text())['ignition_gate_passed']
 records=[]
 for c in cases():
  s,r=make(c);(ROOT/'decks'/f"{c['case']}.fds").write_text(s);records.append(r)
 PLAN.write_text(json.dumps(records,indent=2))
 pre=[]
 for c in cases():
  name=c['case'];w=ROOT/'data/contact_stage_a_preflight'/name;w.mkdir(parents=True,exist_ok=True)
  s,r=make(c,1.05);(w/'check.fds').write_text(s)
  with (w/'run.log').open('w') as f:p=subprocess.run([str(BINARY),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=180)
  assert p.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower(),name
  with (w/(name+'_devc.csv')).open() as f:
   it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];rows=[dict(zip(keys,map(float,v))) for v in it if v]
  mass=sum(v for k,v in rows[1].items() if k.startswith('mass '));expected=r['nominal_dry_fuel_kg']*1.14
  assert abs(mass-expected)<max(.01,.15*expected),(name,mass,expected)
  pre.append(dict(case=name,passed=True,initial_mass_kg=mass));print('PREFLIGHT',name,flush=True)
 (ROOT/'results/contact-stage-a-preflight.json').write_text(json.dumps(pre,indent=2))
 # Six controllers, each at most one VM. Fine/expanded jobs start promptly.
 chains=[['ac21_double_fine'],['ac21_double_expanded'],['ac21_single_expanded'],['ac21_corner_expanded'],['ac21_single','ac21_double'],['ac21_bare','ac21_corner']]
 lookup={r['case']:r for r in records}
 for idx,chain in enumerate(chains):
  steps=[]
  for j,name in enumerate(chain):
   r=lookup[name];w=json.loads((ROOT.parent/'20_composition_iterative/workflow_template.json').read_text());hours=r['hours'];seconds=round(hours*3600)
   runner=(ROOT.parent/'20_composition_iterative/runner.py').read_text().replace("'composition19/'",repr('contact-stage-a/'+name+'/')).replace('50*1024**2','200*1024**2')
   worker="import json\nfrom pathlib import Path\nimport runner\nPath('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)\nc=json.loads(Path('/study/case.json').read_text())\nr=runner.run(c,"+str(seconds-600)+")\nprint('CASE_DONE',r['full_horizon'],flush=True)\n"
   payload={'runner.py':runner,'worker.py':worker,'case.json':json.dumps(r),'decks/'+name+'.fds':(ROOT/'decks'/f'{name}.fds').read_text()}
   payload={k:base64.b64encode(v.encode()).decode() for k,v in payload.items()}
   bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
   ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + '+str(seconds-300)+'}';job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(seconds-450)+'s';task['runnables'][0]['container']['commands']=['-c',bootstrap]
   label=name.replace('_','-');job['labels']['trial_id']=label;job['allocationPolicy']['labels']['trial_id']=label
   raw=json.dumps(w).replace('fds-controlled-trial','fds-'+label).replace('domain17/job-status.json','contact-stage-a/'+name+'/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+label)
   part=json.loads(raw)['main']['steps']
   if j<len(chain)-1:part=part[:-1]
   def rename(x):
    if isinstance(x,list):return [rename(v) for v in x]
    if isinstance(x,dict):
     return {k:('s'+str(j)+'_'+v if k=='next' and v not in ['end','continue','break'] else [{('s'+str(j)+'_'+next(iter(st))):rename(next(iter(st.values())))} for st in v] if k=='steps' else rename(v)) for k,v in x.items()}
    return x
   steps.extend(rename({'steps':part})['steps'])
  folder=ROOT/'jobs'/f'contact-chain-{idx}';folder.mkdir(exist_ok=True)
  (folder/'workflow.yaml').write_text(yaml.safe_dump({'main':{'steps':steps}},sort_keys=False))
  (folder/'spec.json').write_text(json.dumps(dict(workflow=f'fds-ac21-chain-{idx}',cases=chain),indent=2))
 print('Prepared eight cases in six bounded controllers; total12 VM-hours, $1.50 allowance.')

def launch():
 assert all(r['passed'] for r in json.loads((ROOT/'results/contact-stage-a-preflight.json').read_text()))
 with (ROOT/'data/contact-stage-a.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  assert not BUDGET.exists(),'Reservation already exists; no automatic resubmission'
  assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1'),'Existing work'
  for w in gc('workflows','list','--location=us-central1'):
   assert not gc('workflows','executions','list',w['name'].split('/')[-1],'--location=us-central1','--filter=state=ACTIVE')
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  folders=sorted((ROOT/'jobs').glob('contact-chain-*'))
  for folder in folders:
   spec=json.loads((folder/'spec.json').read_text());source=folder/'workflow.yaml'
   gc('workflows','deploy',spec['workflow'],'--location=us-central1','--source='+str(source),'--service-account='+sa)
   assert yaml.safe_load(gc('workflows','describe',spec['workflow'],'--location=us-central1')['sourceContents'])==yaml.safe_load(source.read_text())
  ledger=dict(total_authorized_usd=1.5,scope='User go for corrected eight-case Stage A rerun; six concurrent VMs due24 C3 CPU quota',reserved_usd=1.5,reserved_vm_hours=12,compute_rate_ceiling=.08,ancillary_allowance=.54,automatic_retries=False,reserved_unix=time.time(),cases=json.loads(PLAN.read_text()),executions=[])
  BUDGET.write_text(json.dumps(ledger,indent=2))
  for folder in folders:
   spec=json.loads((folder/'spec.json').read_text());r=gc('workflows','execute',spec['workflow'],'--location=us-central1');(folder/'execution.json').write_text(json.dumps(r,indent=2));ledger['executions'].append(r['name']);BUDGET.write_text(json.dumps(ledger,indent=2));print('SUBMITTED',spec['cases'],r['name'],flush=True)
if __name__=='__main__':
 import sys
 {'prepare':prepare,'launch':launch}[sys.argv[1]]()
