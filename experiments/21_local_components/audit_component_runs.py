import json,math,subprocess,sys
import numpy as np
from scene import ROOT
from extract_component_states import devices
for name in sys.argv[1:]:
 folder=ROOT/'data/cloud'/name;d=devices(folder,name);r=json.loads((folder/'result.json').read_text());raw=json.loads((ROOT/'data/component_states'/(name+'.json')).read_text());end=float(d['Time'][-1]);out=ROOT/'data/boundary'/name;out.mkdir(exist_ok=True);vals=[];all_values=[]
 for face in [-1,1,-2,2,-3,3]:
  p=out/f'burn_{face}.csv'
  if not p.exists():
   z=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=f'{name}\n3\n1\nn\n0 {end}\n{face}\n1\n5\n{p}\n',text=True,capture_output=True,timeout=120,check=True);p.with_suffix('.log').write_text(z.stdout+z.stderr)
  for line in p.read_text().splitlines():
   try:v=list(map(float,line.split(',')))
   except ValueError:continue
   if len(v)==4 and math.isfinite(v[3]):all_values.append(v[3])
   if len(v)==4 and math.isfinite(v[3]) and 23.99<=v[0]<=24.51 and 7.99<=v[1]<=16.01 and -.01<=v[2]<=6.01:vals.append(v[3])
 assert vals
 nodes=[]
 for i,n in enumerate(raw['configuration']['canopies']):
  fuel=sum(v for k,v in d.items() if k.startswith(n['id']+' fuel '));t=d['Time'];mask=t>=22
  nodes.append(dict(id=n['id'],initialized=n['initialized'],fuel_22_to_end_kg=float(np.trapezoid(fuel[mask],t[mask])),max_midpoint_mass_discrepancy_kg=max(abs(f['canopies'][i]['mass_discrepancy_kg']) for f in raw['particle_frames'] if .5<=f['time_s']<=end-.5)))
 report=dict(case=name,complete=r['full_horizon'],physical_seconds=end,wall_seconds=r['wall_seconds'],raw_facade_mean_burn_max=max(vals),raw_all_structure_mean_burn_max=max(all_values),facade_device_burn_max=float(max(d['house_burn_max'])),facade_temperature_max_C=float(max(d['house_max'])),canopies=nodes,ignitors_remaining_after22=max(n for t,n in raw['ignitors'] if t>=22),timing_note='Particle snapshots instantaneous; devices time-averaged by default (read.f90 TIME_AVERAGED=true). Midpoint alignment approximates interval averaging; not exact during rapid transients.')
 (ROOT/'results'/(name+'-audit.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report))
