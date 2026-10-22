"""Collect and assess exactly one follow-up; never launch or retry a simulation."""
import csv,fcntl,json,time,traceback
from pathlib import Path
import numpy as np
from upwind_test import ROOT,FOLDER,NAME
from control import gc,fetch

def read(suffix):
 with (ROOT/'data/cloud'/NAME/(NAME+suffix)).open() as f:
  it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];a=np.array([list(map(float,row)) for row in it if row]);return {k:a[:,i] for i,k in enumerate(keys)}
def main():
 e=json.loads((FOLDER/'execution.json').read_text())['name'].split('/')
 while True:
  s=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');(FOLDER/'status.json').write_text(json.dumps(s,indent=2))
  if s['state']!='ACTIVE':break
  time.sleep(60)
 fetch();r=json.loads((ROOT/'data/cloud'/NAME/'result.json').read_text());h=read('_hrr.csv');d=read('_devc.csv')
 report=dict(case=NAME,complete=r['full_horizon'],wall_seconds=r['wall_seconds'],physical_seconds=r['physical_seconds_reached'],no_more_runs_authorized=True)
 if r['full_horizon']:
  t=np.arange(40,60.01,.1);q=np.interp(t,h['Time'],h['HRR']);min10=float(min(q[t<=50]));energy=float(np.trapezoid(q,t)/1000);burn=bool(np.any(d['house_burn_max']>1e-9));fuel=sum(d[k] for k in d if k.startswith('fuel_release '));ft=np.interp(t,d['Time'],fuel)
  report.update(minimum_hrr_40_50_kw=min10,energy_40_60_MJ=energy,vegetation_fuel_release_40_60_kg=float(np.trapezoid(np.maximum(ft,0),t)),house_device_burning=burn,peak_house_C=float(max(d['house_max'])),sustained_total_hrr_gate=min10>=100 and energy>=1,vegetation_attribution='Check fuel-release and building-burning channels; HRR alone is not sufficient if the building burns.')
 (ROOT/'results/upwind-result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':
 with (ROOT/'data/upwind-finish.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:main()
  except Exception:
   (ROOT/'results/upwind-error.txt').write_text(traceback.format_exc());raise
