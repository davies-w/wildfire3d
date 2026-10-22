"""Final sampling-isolation decision using archived outputs, without new solves."""
import csv,json,datetime
import numpy as np
from scipy.io import FortranFile,FortranEOFError
from scene import ROOT
names=['ac21_double','sampling21_dense','ac21_double_fine'];rows=[]
for name in names:
 folder=ROOT/'data/cloud'/name
 with (folder/(name+'_devc.csv')).open() as f:
  r=csv.reader(f);next(r);keys=[k.strip().strip('"') for k in next(r)];v=np.array([list(map(float,row)) for row in r]);d=dict(zip(keys,v.T))
 mass=sum(v for k,v in d.items() if k.startswith('mass '));first=int(np.flatnonzero(mass>0)[0])
 f=FortranFile(folder/(name+'_1.prt5'));f.read_ints();f.read_ints();nc=int(f.read_ints()[0]);labels=[]
 for c in range(nc):
  nq=int(f.read_ints()[0]);q=[]
  for j in range(nq):q.append(bytes(f.read_record('u1')).decode().strip());f.read_record('u1')
  labels.append(q)
 peaks={'small':-1.,'large':-1.};post={'small':-1.,'large':-1.};igniters=[]; early=[]
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  for c in range(nc):
   n=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,n);f.read_ints();q=f.read_reals('f4').reshape(len(labels[c]),n) if labels[c] else None
   if c==4 and t>=22:igniters.append(n)
   if c!=0 or not n:continue
   temp=q[labels[c].index('PARTICLE TEMPERATURE')]
   for size,mask in [('small',xyz[1]<15),('large',xyz[1]>=15)]:
    if mask.any():
     val=float(max(temp[mask]));peaks[size]=max(peaks[size],val)
     if size=='large' and t<=21:early.append(dict(time_s=t,max_C=val,p95_C=float(np.quantile(temp[mask],.95)),fraction_over300C=float(np.mean(temp[mask]>300))))
     if t>=22:post[size]=max(post[size],val)
 rows.append(dict(case=name,first_nonzero_mass_time_s=float(d['Time'][first]),initial_wet_mass_kg=float(mass[first]),wet_mass_at69_5_kg=float(np.interp(69.5,d['Time'],mass)),foliage_peak_C=peaks,foliage_peak_after22_C=post,igniters_after22_max=max(igniters),large_crown_early=[min(early,key=lambda x:abs(x['time_s']-target)) for target in [5,10,15,20]]))
s=json.loads((ROOT/'jobs/sampling21_dense/status.json').read_text());seconds=(datetime.datetime.fromisoformat(s['endTime'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(s['startTime'].replace('Z','+00:00'))).total_seconds()
report=dict(conclusion='Increasing vegetation particle density eightfold at fixed0.5m gas grid and fuel mass did not reproduce fine-grid large-crown ignition. Particle density alone does not explain the observed ignition switch.',cases=rows,cost=dict(controller_hours_upper=seconds/3600,compute_at_checked_rate_usd=seconds/3600*.079528,including_full_ancillary_allowance_usd=seconds/3600*.079528+.09,reserved_usd=.25,invoice_verified=False),checkpoint='One retained Linux checkpoint hash verified; native startup/resume previously tested. Linux checkpoint resume has not been exercised.',limitations=['One seed; different sampling positions remain. This does not isolate fluid-grid heat transfer from every other mesh-dependent effect.','Fine-grid case only69.5s. Fine no-vegetation source control was not run; fine facade ignition precedes igniter removal.','Generic unvalidated vegetation/materials and prescribed hot sources; no trunks/ground cover/embers.'],next_step='Early raw particle histories locate divergence during initialization. Only a y=12 gas slice was saved, so no large-crown y=18 gas slice exists to prove the local gas-heating mechanism. Smallest proposed paid follow-up is the already prepared stronger large-ring source trial ($0.125 planning allowance), explicitly initialization calibration; hold coarse grid and fuel sampling fixed, measure each crown, and do not infer physical accuracy from successful ignition. Do not merely add particles or proceed to Stage B. Keep any stronger-source trial labelled initialization calibration, not accuracy validation.')
(ROOT/'results/sampling-final-diagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
