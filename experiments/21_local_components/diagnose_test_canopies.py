"""Post-freeze test diagnosis from raw per-canopy devices and particle evidence; no refit."""
import json,sys
import numpy as np
from scene import ROOT
from extract_component_states import devices
for name in sys.argv[1:]:
 raw=json.loads((ROOT/'data/component_test_states'/f'{name}.json').read_text());d=devices(ROOT/'data/cloud'/name,name);t=d['Time'];rows=[]
 for i,n in enumerate(raw['configuration']['canopies']):
  fuel=sum(v for k,v in d.items() if k.startswith(n['id']+' fuel '));windows={}
  for lo,hi in [(0,20),(22,90),(30,60),(60,90)]:
   mask=(t>=lo)&(t<=hi);windows[f'{lo}_{hi}']=dict(fuel_kg=float(np.trapezoid(fuel[mask],t[mask])),peak_kg_s=float(fuel[mask].max()),mean_kg_s=float(fuel[mask].mean()))
  snapshots=[]
  for at in [0,20,22,30,60,90]:
   frame=min(raw['particle_frames'],key=lambda f:abs(f['time_s']-at));classes=frame['canopies'][i]['classes'];snapshots.append(dict(time_s=frame['time_s'],wet_mass_kg=sum(c['represented_mass_kg'] for c in classes),max_particle_temperature_C=max(c['temperature_max_C'] for c in classes),mass_above500kg=sum(c['mass_above500_kg'] for c in classes)))
  rows.append(dict(id=n['id'],initialized=n['initialized'],windows=windows,snapshots=snapshots))
 out=dict(case=name,configuration=raw['configuration'],ignitors_remaining_after22=max(num for time,num in raw['ignitors'] if time>=22),canopies=rows,scope='Raw device fuel-release windows and represented particle snapshots. Wet-mass loss includes moisture and cannot alone be called burned fuel. Test outcomes are not used to change frozen predictions.')
 (ROOT/'results'/f'{name}-canopy-diagnosis.json').write_text(json.dumps(out,indent=2));print(name,json.dumps(rows,indent=2))
