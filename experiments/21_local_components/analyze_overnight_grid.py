"""Analyze collected cases only. Partial results remain explicitly incomplete."""
import json,math,subprocess
import numpy as np
from scene import ROOT
from finish_sampling import read,comparison
from overnight_grid_control import cases

def run():
 reports=[]
 for c in cases():
  name=c['case'];dest=ROOT/'data/cloud'/name
  if not (ROOT/'results'/(name+'-collected.json')).exists():continue
  result=json.loads((dest/'result.json').read_text());d=read(name);end=float(d['Time'][-1]);boundary=ROOT/'data/boundary'/name;boundary.mkdir(exist_ok=True);values=[]
  for face in [-1,1,-2,2,-3,3]:
   out=boundary/f'burn_{face}.csv'
   if not out.exists():
    p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=dest,input=f'{name}\n3\n1\nn\n0 {end}\n{face}\n1\n5\n{out}\n',text=True,capture_output=True,timeout=120,check=True);out.with_suffix('.log').write_text(p.stdout+p.stderr)
   for line in out.read_text().splitlines():
    try:v=list(map(float,line.split(',')))
    except ValueError:continue
    if len(v)==4 and math.isfinite(v[3]) and 15.99<=v[0]<=16.51 and 7.99<=v[1]<=16.01 and -.01<=v[2]<=6.01:values.append(v[3])
  assert values,'No raw facade values'
  crowns={}
  for tag in ['small','large']:
   mass=sum(v for k,v in d.items() if k.startswith(tag+' mass '));fuel=sum(v for k,v in d.items() if k.startswith(tag+' fuel '));t=d['Time'];mask=(t>=22)&(t<=end)
   crowns[tag]=dict(wet_mass_at21_kg=float(np.interp(21,t,mass)) if end>=21 else None,wet_mass_at_end_kg=float(mass[-1]),fuel_release_22_to_end_kg=float(np.trapezoid(fuel[mask],t[mask])) if mask.sum()>1 else None)
  hits=d['Time'][d['house_burn_max']>1e-9]
  reports.append(dict(case=name,complete=result['full_horizon'],horizon_reached_s=end,wall_seconds=result['wall_seconds'],first_facade_ignition_s=float(hits[0]) if len(hits) else None,raw_boundary_max_time_mean_burning_rate=max(values),crowns=crowns))
 names={r['case'] for r in reports};comparisons=[]
 if {'overnight21_grid_coarse','overnight21_grid_fine'}<=names:
  end=min(r['horizon_reached_s'] for r in reports if r['case'] in ['overnight21_grid_coarse','overnight21_grid_fine']);comparisons.append(comparison('overnight21_grid_coarse','overnight21_grid_fine',np.floor(end*2)/2))
 (ROOT/'results/overnight-grid-results.json').write_text(json.dumps(dict(cases=reports,comparisons=comparisons,limits='40s initialization diagnostics, not180s Stage A validation. Generic materials, synthetic facade, no trunks/groundcover/embers. Source-only control does not isolate all nonlinear source/vegetation interactions. Gas slices and particle archives still require mechanism-specific inspection.'),indent=2))
 print('Analyzed',len(reports),'collected cases')
if __name__=='__main__':run()
