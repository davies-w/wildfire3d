"""Single collector for sampling isolation; never submits or retries jobs."""
import csv,fcntl,json,math,subprocess,tarfile,time,traceback
from pathlib import Path
import numpy as np
from scene import ROOT
from control import gc,G
from sampling_test import NAME,JOB

def read(name,suffix='_devc.csv'):
 with (ROOT/'data/cloud'/name/(name+suffix)).open() as f:
  r=csv.reader(f);next(r);keys=[k.strip().strip('"') for k in next(r)];v=np.array([list(map(float,row)) for row in r]);return dict(zip(keys,v.T))
def comparison(a,b,end):
 da,db=read(a),read(b);t=np.arange(0,end+.01,.5);details=[]
 for k in da:
  if not k.startswith('p') or not k.endswith('_temp'):continue
  stem=k[:-5]
  def tr(d):
   temp=np.interp(t,d['Time'],d[k]);rad=np.interp(t,d['Time'],d[stem+'_rad_in']);conv=np.interp(t,d['Time'],d[stem+'_conv']);hits=t[np.interp(t,d['Time'],d[stem+'_burn'])>1e-9];return temp,float(np.trapezoid(np.maximum(rad-d[stem+'_rad_in'][0],0)+np.maximum(conv,0),t)),float(hits[0]) if len(hits) else None
  ta,qa,ia=tr(da);tb,qb,ib=tr(db);rel=abs(qa-qb)/max(qb,100);mae=float(np.mean(abs(ta-tb)));flip=(ia is None)!=(ib is None);dt=abs(ia-ib) if ia is not None and ib is not None else None
  details.append(dict(probe=stem,relative_dose_error=rel,temperature_mae_C=mae,ignition_flip=flip,ignition_dt_s=dt,failed=(max(qa,qb)>=100 and rel>.1) or mae>25 or flip or (dt is not None and dt>5)))
 return dict(candidate=a,reference=b,horizon_s=end,failed_probes=sum(p['failed'] for p in details),ignition_flips=sum(p['ignition_flip'] for p in details),max_dose_error=max(p['relative_dose_error'] for p in details),max_temperature_mae_C=max(p['temperature_mae_C'] for p in details),probes=details)
def run():
 e=json.loads((JOB/'execution.json').read_text())['name'].split('/')
 while True:
  r=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');(JOB/'status.json').write_text(json.dumps(r,indent=2))
  if r['state']!='ACTIVE':break
  time.sleep(120)
 inventory={k:gc(*a) for k,a in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};(ROOT/'results/sampling-cleanup.json').write_text(json.dumps(inventory,indent=2));assert not any(inventory.values()),'Cleanup incomplete'
 archive=ROOT/'data/downloads'/(NAME+'.tar.gz')
 if not archive.exists():subprocess.run([G,'storage','cp',f'gs://tmrw-wildfire-20261015-trial/sampling21/{NAME}/{NAME}.tar.gz',str(archive)],check=True)
 dest=ROOT/'data/cloud'/NAME
 if not (dest/'result.json').exists():
  with tarfile.open(archive) as t:t.extractall(dest.parent,filter='data')
 result=json.loads((dest/'result.json').read_text());d=read(NAME);end=min(69.5,float(d['Time'][-1]));end=np.floor(end*2)/2
 manifest=json.loads((dest/'checkpoint-manifest.json').read_text());import hashlib
 for c in manifest['files']:assert hashlib.sha256((dest/c['name']).read_bytes()).hexdigest()==c['sha256']
 boundary=ROOT/'data/boundary'/NAME;boundary.mkdir(exist_ok=True);vals=[]
 for face in [-1,1,-2,2,-3,3]:
  out=boundary/f'burn_{face}.csv'
  if not out.exists():
   p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=dest,input=f'{NAME}\n3\n1\nn\n0 {end}\n{face}\n1\n5\n{out}\n',text=True,capture_output=True,timeout=90,check=True);out.with_suffix('.log').write_text(p.stdout+p.stderr)
  for line in out.read_text().splitlines():
   try:v=list(map(float,line.split(',')))
   except ValueError:continue
   if len(v)==4 and math.isfinite(v[3]) and 15.99<=v[0]<=16.51 and 7.99<=v[1]<=16.01 and -.01<=v[2]<=6.01:vals.append(v[3])
 crowns={}
 for tag in ['small','large']:
  m=sum(v for k,v in d.items() if k.startswith(tag+' mass '));fuel=sum(v for k,v in d.items() if k.startswith(tag+' fuel '));t=np.arange(22,min(60,end)+.01,.1)
  crowns[tag]=dict(wet_mass_21_40_60_kg=np.interp([21,min(40,end),min(60,end)],d['Time'],m).tolist(),fuel_release_22_60_kg=float(np.trapezoid(np.interp(t,d['Time'],fuel),t)) if len(t)>1 else None)
 hits=d['Time'][d['house_burn_max']>1e-9]
 report=dict(complete=result['full_horizon'],physical_seconds=result['physical_seconds_reached'],wall_seconds=result['wall_seconds'],first_house_ignition_s=float(hits[0]) if len(hits) else None,raw_boundary_max_mean_burning_rate=max(vals),comparison_horizon_s=end,crowns=crowns,comparisons=[comparison(NAME,b,end) for b in ['ac21_double','ac21_double_fine']],checkpoint_files_verified=len(manifest['files']),reserved_usd=.25,invoice_verified=False,no_stage_b_training=True,limitations=['Same coarse gas grid and source; eightfold vegetation particle density. Nominal density matches fine case, not identical placement/voxelized canopy.','Generic vegetation/wood, artificial ignition, no trunks/ground cover/embers.','Native resume tested locally; actual saved Linux checkpoints require matching Linux binary.'])
 (ROOT/'results/sampling-result.json').write_text(json.dumps(report,indent=2));print('DONE',report['complete'],flush=True)
 subprocess.run([str(ROOT.parents[1]/'.venv/bin/dvc'),'commit','-f','sampling_cloud'],cwd=ROOT,check=True)
if __name__=='__main__':
 with (ROOT/'data/sampling-finish.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (ROOT/'results/sampling-result.json').exists(),'Already collected'
  try:run()
  except Exception:
   (ROOT/'results/sampling-error.txt').write_text(traceback.format_exc());raise
