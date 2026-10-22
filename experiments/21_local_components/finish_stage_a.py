"""One-shot continuation, bounded to authorized Stage A. Never retry paid cases."""
import csv,fcntl,json,math,subprocess,time,traceback
from pathlib import Path
import numpy as np
from scene import ROOT,deck
import control

def devices(name):
 p=ROOT/'data/cloud'/name/(name+'_devc.csv')
 with p.open() as f:
  it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];values=np.array([list(map(float,row)) for row in it if row])
 assert np.isfinite(values).all() and values[-1,0]>=180
 return {k:values[:,i] for i,k in enumerate(keys)}
def boundary(name):
 folder=ROOT/'data/cloud'/name;outdir=ROOT/'data/boundary'/name;outdir.mkdir(parents=True,exist_ok=True);vals=[]
 for face in (-1,1,-2,2,-3,3):
  out=outdir/f'burning_{face}.csv'
  if not out.exists():
   answer=f'{name}\n3\n1\nn\n0 180\n{face}\n1\n5\n{out}\n'
   p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=answer,text=True,capture_output=True,timeout=90,check=True);out.with_suffix('.log').write_text(p.stdout+p.stderr)
  for line in out.read_text().splitlines():
   try:v=list(map(float,line.split(',')))
   except ValueError:continue
   if len(v)==4 and math.isfinite(v[3]) and 15.49<=v[0]<=24.01 and 7.49<=v[1]<=16.51 and -.01<=v[2]<=6.51:vals.append(v[3])
 assert vals,'No raw building boundary samples'
 return dict(maximum_0_180_mean_burning_rate=max(vals),samples=len(vals))
def audit(name):
 r=json.loads((ROOT/'data/cloud'/name/'result.json').read_text());assert r['full_horizon'],name+' incomplete'
 d=devices(name);b=boundary(name);hits=d['Time'][d['house_burn_max']>1e-9]
 assert (b['maximum_0_180_mean_burning_rate']>1e-12)==bool(len(hits)),'Boundary/device disagreement'
 return dict(case=name,first_ignition_s=float(hits[0]) if len(hits) else None,peak_house_C=float(max(d['house_max'])),raw_boundary=b,wall_seconds=r['wall_seconds'],cpu_s=r['cpu_user_s']+r['cpu_system_s'])
def wait_done():
 while True:
  rows=control.status()
  if rows and all(r['state']!='ACTIVE' for r in rows):return
  time.sleep(60)
def compare(a,b):
 da,db=devices(a),devices(b);grid=np.arange(0,180.01,.5);details=[]
 for k in da:
  if not k.startswith('p') or not k.endswith('_temp'):continue
  stem=k[:-5]
  def traces(d):
   temp=np.interp(grid,d['Time'],d[k]);rad=np.interp(grid,d['Time'],d[stem+'_rad_in']);conv=np.interp(grid,d['Time'],d[stem+'_conv']);burn=np.interp(grid,d['Time'],d[stem+'_burn']);dose=float(np.trapezoid(np.maximum(rad-rad[0],0)+np.maximum(conv,0),grid));hit=grid[burn>1e-9]
   return temp,dose,float(hit[0]) if len(hit) else None
  ta,qa,ia=traces(da);tb,qb,ib=traces(db);exposed=max(qa,qb)>=100
  relative=abs(qa-qb)/max(qb,100);mae=float(np.mean(abs(ta-tb)));flip=(ia is None)!=(ib is None);dt=abs(ia-ib) if ia is not None and ib is not None else None
  passed=(not exposed or relative<=.1) and mae<=25 and not flip and (dt is None or dt<=5)
  details.append(dict(probe=stem,compact_dose_kj_m2=qa,reference_dose_kj_m2=qb,absolute_dose_error_kj_m2=abs(qa-qb),relative_dose_error=relative,exposed=exposed,temperature_mae_C=mae,ignition_flip=flip,ignition_time_difference_s=dt,passed=passed))
 return dict(compact=a,reference=b,passed=all(r['passed'] for r in details),probes=details)
def run():
 wait_done();control.fetch();first=json.loads((ROOT/'wave1.json').read_text());audits=[audit(r['case']) for r in first]
 gate=dict(allow_wave2=True,scope='Complete finite first-wave evidence with boundary/device agreement; not a physics validation',cases=audits)
 (ROOT/'results/wave1-gate.json').write_text(json.dumps(gate,indent=2))
 strongest=max([r for r in audits if r['case']!='a21_bare'],key=lambda r:r['peak_house_C'])['case'];second=[];pairs=[]
 for r in first:
  if r['kind']=='bare':continue
  s=dict(r,case=r['case']+'_expanded',expanded=True);second.append(s);pairs.append((r['case'],s['case']))
 r=next(r for r in first if r['case']==strongest);s=dict(r,case=r['case']+'_fine',dx=.25);second.append(s);pairs.append((r['case'],s['case']))
 (ROOT/'wave2.json').write_text(json.dumps(second,indent=2));(ROOT/'comparison-pairs.json').write_text(json.dumps(pairs))
 # Validate all new geometries locally before any second-wave paid submission.
 import os
 binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
 for c in second:
  w=ROOT/'data/preflight2'/c['case'];w.mkdir(parents=True,exist_ok=True);text,_=deck(c,horizon=.1);(w/'check.fds').write_text(text)
  with (w/'run.log').open('w') as f:p=subprocess.run([str(binary),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=240)
  assert p.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower(),'Second-wave preflight failed'
 control.prepare(second,2);control.launch(2);wait_done();control.fetch();audits.extend(audit(r['case']) for r in second)
 comparisons=[compare(*p) for p in pairs];report=dict(status='complete',passed_context_resolution=all(r['passed'] for r in comparisons),cases=audits,comparisons=comparisons,any_positive=any(r['first_ignition_s'] is not None for r in audits),any_negative=any(r['first_ignition_s'] is None for r in audits),no_training_started=True)
 (ROOT/'results/stage-a.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('cases','comparisons')}),flush=True)
if __name__=='__main__':
 with (ROOT/'data/finish.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if (ROOT/'results/stage-a.json').exists():raise RuntimeError('Already completed; do not repeat')
  try:run()
  except Exception:
   (ROOT/'results/continuation-error.txt').write_text(traceback.format_exc());raise
