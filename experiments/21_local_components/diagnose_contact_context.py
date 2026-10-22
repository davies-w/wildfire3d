"""Locate when compact/expanded discrepancies emerge; no new simulations."""
import csv,json
from pathlib import Path
import numpy as np
from scene import ROOT

def read(name,suffix):
 with (ROOT/'data/cloud'/name/(name+suffix)).open() as f:
  r=csv.reader(f);next(r);keys=[k.strip().strip('"') for k in next(r)];v=np.array([list(map(float,row)) for row in r]);return dict(zip(keys,v.T))
rows=[]
for kind in ['single','double','corner']:
 a='ac21_'+kind;b=a+'_expanded';da,db=read(a,'_devc.csv'),read(b,'_devc.csv');ha,hb=read(a,'_hrr.csv'),read(b,'_hrr.csv');end=np.floor(min(da['Time'][-1],db['Time'][-1])*2)/2
 row=dict(kind=kind,horizon=end,windows=[])
 for start,stop in [(0,20),(22,40),(40,60),(60,end)]:
  t=np.arange(start,stop+.01,.5);probes=[]
  for k in da:
   if not k.startswith('p') or not k.endswith('_temp'):continue
   stem=k[:-5]
   def trace(d):
    temp=np.interp(t,d['Time'],d[k]);rad=np.interp(t,d['Time'],d[stem+'_rad_in']);conv=np.interp(t,d['Time'],d[stem+'_conv']);base=d[stem+'_rad_in'][0];dose=float(np.trapezoid(np.maximum(rad-base,0)+np.maximum(conv,0),t));return temp,dose
   ta,qa=trace(da);tb,qb=trace(db);probes.append(dict(probe=stem,temp_mae=float(np.mean(abs(ta-tb))),dose_relative=abs(qa-qb)/max(qb,100),exposed=max(qa,qb)>=100))
  mass=lambda d:sum(v for k,v in d.items() if k.startswith('mass '))
  row['windows'].append(dict(start=start,stop=stop,max_probe_temperature_mae=max(p['temp_mae'] for p in probes),exposed_probes_over10pct=sum(p['exposed'] and p['dose_relative']>.1 for p in probes),compact_total_energy_MJ=float(np.trapezoid(np.interp(t,ha['Time'],ha['HRR']),t)/1000),expanded_total_energy_MJ=float(np.trapezoid(np.interp(t,hb['Time'],hb['HRR']),t)/1000),compact_remaining_particle_mass_kg=float(np.interp(stop,da['Time'],mass(da))),expanded_remaining_particle_mass_kg=float(np.interp(stop,db['Time'],mass(db)))))
 rows.append(row)
report=dict(cases=rows,interpretation='Descriptive timing diagnosis only; domain size and rear building mass changed together. Total HRR includes building burning. Wet particle mass is not fuel vapour. Incomplete expanded cases do not pass Stage A.',next_isolation='Hold compact building geometry fixed, enlarge only external mesh, keep ignition/wind/materials identical. Do not launch without a new cost allowance.')
(ROOT/'results/contact-context-diagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows,indent=2))
