"""Final partial-horizon refinement audit, preserving censored evidence."""
import csv,json,math,subprocess,datetime
import numpy as np
from scene import ROOT

def read(name):
 with (ROOT/'data/cloud'/name/(name+'_devc.csv')).open() as f:
  r=csv.reader(f);next(r);keys=[k.strip().strip('"') for k in next(r)];v=np.array([list(map(float,row)) for row in r]);return dict(zip(keys,v.T))
a='ac21_double';b='ac21_double_fine';da,db=read(a),read(b);end=69.5;t=np.arange(0,end+.01,.5);details=[]
for k in da:
 if not k.startswith('p') or not k.endswith('_temp'):continue
 stem=k[:-5]
 def trace(d):
  temp=np.interp(t,d['Time'],d[k]);rad=np.interp(t,d['Time'],d[stem+'_rad_in']);conv=np.interp(t,d['Time'],d[stem+'_conv']);hit=t[np.interp(t,d['Time'],d[stem+'_burn'])>1e-9]
  return temp,float(np.trapezoid(np.maximum(rad-d[stem+'_rad_in'][0],0)+np.maximum(conv,0),t)),float(hit[0]) if len(hit) else None
 ta,qa,ia=trace(da);tb,qb,ib=trace(db);rel=abs(qa-qb)/max(qb,100);mae=float(np.mean(abs(ta-tb)));flip=(ia is None)!=(ib is None);dt=abs(ia-ib) if ia is not None and ib is not None else None
 details.append(dict(probe=stem,relative_dose_error=rel,temperature_mae_C=mae,ignition_flip=flip,ignition_dt_s=dt,failed=(max(qa,qb)>=100 and rel>.1) or mae>25 or flip or (dt is not None and dt>5)))
folder=ROOT/'data/cloud'/b;dest=ROOT/'data/boundary'/b;dest.mkdir(exist_ok=True);vals=[]
for face in [-1,1,-2,2,-3,3]:
 out=dest/f'partial_burn_{face}.csv'
 if not out.exists():
  p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=f'{b}\n3\n1\nn\n0 {end}\n{face}\n1\n5\n{out}\n',text=True,capture_output=True,check=True,timeout=90);out.with_suffix('.log').write_text(p.stdout+p.stderr)
 for line in out.read_text().splitlines():
  try:v=list(map(float,line.split(',')))
  except ValueError:continue
  if len(v)==4 and math.isfinite(v[3]) and 15.99<=v[0]<=16.51 and 7.99<=v[1]<=16.01 and -.01<=v[2]<=6.01:vals.append(v[3])
assert vals and max(vals)>0
r=json.loads((folder/'result.json').read_text());hits=db['Time'][db['house_burn_max']>1e-9]
seconds=0
for p in (ROOT/'jobs').glob('contact-chain-*/status.json'):
 s=json.loads(p.read_text());seconds+=(datetime.datetime.fromisoformat(s['endTime'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(s['startTime'].replace('Z','+00:00'))).total_seconds()
report=dict(stage_a_passed=False,full_horizon_cases=4,censored_cases=4,fine=dict(physical_seconds=r['physical_seconds_reached'],wall_seconds=r['wall_seconds'],first_house_ignition_s=float(hits[0]),peak_house_C=float(max(db['house_max'])),maximum_boundary_mean_burning_rate_0_69_5=max(vals),coarse_mass_at69_5=float(sum(np.interp(end,da['Time'],v) for k,v in da.items() if k.startswith('mass '))),fine_mass_at69_5=float(sum(np.interp(end,db['Time'],v) for k,v in db.items() if k.startswith('mass ')))),partial_comparison=dict(horizon_s=end,failed_probes=sum(p['failed'] for p in details),ignition_flips=sum(p['ignition_flip'] for p in details),max_dose_error=max(p['relative_dose_error'] for p in details),max_temperature_mae_C=max(p['temperature_mae_C'] for p in details),probes=details),cost=dict(controller_hours_upper=seconds/3600,compute_at_planning_price_usd=seconds/3600*.079528,including_full_ancillary_allowance_usd=seconds/3600*.079528+.54,invoice_verified=False,reserved_usd=1.5),cleanup=json.loads((ROOT/'results/contact-stage-a-cleanup.json').read_text()),next_step='Do not proceed to Stage B. First isolate vegetation particle sampling at fixed coarse gas grid and source; keep domain-only isolation as a separate follow-up. Large-crown ignition is grid sensitive; source calibration must be tested across grids, not assumed from coarse startup.',limitations=['Same physical ignition source and seed, but .25m grid also increases particle sampling (one per cell); this is a coupled mesh/particle refinement, not pure fluid-grid convergence.','Incomplete 69.5s comparison cannot pass180s acceptance.','Generic material/analytic canopy, artificial contact ignition, no trunks, ground cover or embers.','No resumable restart preserved in this run.'])
(ROOT/'results/contact-stage-a-final-diagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='partial_comparison'},indent=2));print('COMPARISON', {k:v for k,v in report['partial_comparison'].items() if k!='probes'})
