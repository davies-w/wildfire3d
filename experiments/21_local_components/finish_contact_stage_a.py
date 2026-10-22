"""One-shot result collection; never submits or retries a cloud simulation."""
import csv,fcntl,json,subprocess,tarfile,time,traceback
import numpy as np
from scene import ROOT
from control import gc,G
from finish_stage_a import audit,compare

def run():
 folders=sorted((ROOT/'jobs').glob('contact-chain-*'));assert len(folders)==6
 while True:
  states=[]
  for folder in folders:
   e=json.loads((folder/'execution.json').read_text())['name'].split('/')
   r=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1')
   (folder/'status.json').write_text(json.dumps(r,indent=2));states.append(r['state'])
  if all(s!='ACTIVE' for s in states):break
  time.sleep(120)
 inventory={k:gc(*a) for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
 (ROOT/'results/contact-stage-a-cleanup.json').write_text(json.dumps(inventory,indent=2))
 assert not any(inventory.values()),'Cloud resources remain: inspect cleanup before proceeding'
 cases=[]
 for c in json.loads((ROOT/'contact-stage-a.json').read_text()):
  name=c['case'];archive=ROOT/'data/downloads'/(name+'.tar.gz');archive.parent.mkdir(exist_ok=True)
  if not archive.exists():
   p=subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/contact-stage-a/{name}/{name}.tar.gz',str(archive)],capture_output=True,text=True)
   if p.returncode:
    cases.append(dict(case=name,complete=False,error='No result archive',details=p.stderr[-1000:]));continue
  dest=ROOT/'data/cloud';dest.mkdir(exist_ok=True)
  if not (dest/name/'result.json').exists():
   with tarfile.open(archive) as t:t.extractall(dest,filter='data')
  r=json.loads((dest/name/'result.json').read_text())
  if not r['full_horizon']:
   cases.append(dict(case=name,complete=False,physical_seconds_reached=r['physical_seconds_reached'],stopped_by_budget=r['stopped_by_budget']));continue
  a=dict(audit(name),complete=True)
  def read(suffix):
   with (dest/name/(name+suffix)).open() as f:
    it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];v=np.array([list(map(float,row)) for row in it if row]);return dict(zip(keys,v.T))
  d=read('_devc.csv');h=read('_hrr.csv');m=sum(v for k,v in d.items() if k.startswith('mass '));t=np.arange(40,60.01,.1)
  a.update(wet_particle_mass_loss_40_60_kg=float(np.interp(40,d['Time'],m)-np.interp(60,d['Time'],m)),hrr_min_40_50_kw=float(min(np.interp(t[t<=50],h['Time'],h['HRR']))),energy_40_60_MJ=float(np.trapezoid(np.interp(t,h['Time'],h['HRR']),t)/1000))
  a['sustained_gate']=bool(a['hrr_min_40_50_kw']>=100 and a['energy_40_60_MJ']>=1 and a['wet_particle_mass_loss_40_60_kg']>.1)
  cases.append(a)
 complete={c['case'] for c in cases if c['complete']};pairs=[('ac21_'+k,'ac21_'+k+'_expanded') for k in ['single','double','corner']]+[('ac21_double','ac21_double_fine')]
 comparisons=[compare(a,b) for a,b in pairs if a in complete and b in complete]
 passed=len(complete)==8 and len(comparisons)==4 and all(c['passed'] for c in comparisons) and all(c['sustained_gate'] for c in cases if c['case']!='ac21_bare') and next(c for c in cases if c['case']=='ac21_bare')['first_ignition_s'] is None
 report=dict(status='passed' if passed else 'not_passed',cases=cases,comparisons=comparisons,no_training_started=True,reserved_usd=1.5,invoice_verified=False,limitations=['Artificial contact initialization; generic materials, no trunks/ground cover/embers.','Expanded cases change domain and building mass together.','Total HRR includes facade combustion; wet particle loss is not fuel vapour.','Single seed and assigned canopy geometry; no real-property validation.'])
 (ROOT/'results/contact-stage-a.json').write_text(json.dumps(report,indent=2));print('DONE',report['status'],flush=True)
 subprocess.run([str(ROOT.parents[1]/'.venv/bin/dvc'),'commit','-f','contact_stage_a_cloud'],cwd=ROOT,check=True)
if __name__=='__main__':
 with (ROOT/'data/contact-stage-a-finish.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (ROOT/'results/contact-stage-a.json').exists(),'Already collected'
  try:run()
  except Exception:
   (ROOT/'results/contact-stage-a-error.txt').write_text(traceback.format_exc());raise
