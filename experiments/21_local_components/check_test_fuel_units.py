"""Verify reported test fuel integrals against original FDS units and interval averages."""
import csv,hashlib,json,sys
import numpy as np
from scene import ROOT
for name in sys.argv[1:]:
 p=ROOT/'data/cloud'/name/(name+'_devc.csv')
 with p.open() as f:
  r=csv.reader(f);units=next(r);keys=next(r);a=np.array([list(map(float,row)) for row in r if row])
 report=json.loads((ROOT/'results'/f'{name}-test.json').read_text());nodes=report['models'][0]['canopies'];rows=[]
 for node in nodes:
  ix=[i for i,k in enumerate(keys) if k.startswith(node['id']+' fuel ')];assert len(ix)==4 and all(units[i]=='kg/s' for i in ix);rate=a[:,ix].sum(1);t=a[:,0]
  rows.append(dict(node=node['id'],columns=[keys[i] for i in ix],units=[units[i] for i in ix],integral_interval_average_kg=float(np.sum(rate[1:]*np.diff(t))),integral_raw_timestamp_trapezoid_kg=float(np.trapezoid(rate,t))))
 out=dict(case=name,raw_csv_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),raw_integrals=rows,reported_resampled_fuel=[dict(id=n['id'],reference_kg=n['reference_fuel_release_kg'],prediction_kg=n['predicted_fuel_release_kg']) for n in nodes],definition='DEVC MASS FLUX of FUEL VAPOR, surface-integrated over each PART_ID/SURF_ID class in each canopy; output kg/s. Sum four disjoint fuel classes, integrate seconds to kg. Surrogate power state is this fuel rate times17425kJ/kg, a chemical-energy-release potential proxy, not independently measured gas-phase HRR. Reported model/reference fuel integrals reverse that same scale. Wet-mass loss includes water and is not substituted for fuel release.')
 (ROOT/'results'/f'{name}-fuel-units-check.json').write_text(json.dumps(out,indent=2));print(name,rows)
