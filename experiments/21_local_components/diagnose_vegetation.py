"""Diagnose sustained vegetation burning using native FDS HRR and particle-mass histories."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;rows=[]
for name in ['a21_bare','a21_single','a21_double','a21_corner']:
 provenance={}
 def read(suffix):
  p=ROOT/'data/cloud'/name/(name+suffix);provenance[suffix]=hashlib.sha256(p.read_bytes()).hexdigest()
  with p.open() as f:
   it=csv.reader(f);next(it);keys=next(it);a=np.array([list(map(float,v)) for v in it if v]);return {k.strip():a[:,i] for i,k in enumerate(keys)}
 d=read('_devc.csv');h=read('_hrr.csv');m=sum(d[k] for k in d if k.startswith('mass '));mask=h['Time']>=30
 rows.append(dict(case=name,initial_wet_particle_mass_kg=float(m[1]),final_particle_mass_kg=float(m[-1]),mass_loss_fraction=float((m[1]-m[-1])/m[1]) if m[1] else None,hrr_at_30s_kw=float(np.interp(30,h['Time'],h['HRR'])),energy_30_to_180_MJ=float(np.trapezoid(h['HRR'][mask],h['Time'][mask])/1000),file_sha256=provenance))
report=dict(finding='No substantial sustained vegetation fire after burner shutdown at21 s.',caveats=['Particle mass loss includes water loss and cannot be treated as dry fuel consumed.','Trace heat release does not establish an exactly zero local ignition event.','No matched material sensitivity run: material causation unproven.','Burner/crown separation and wind-advection explanation is a hypothesis; plume and particle-temperature inspection needed.'],cases=rows)
(ROOT/'results/vegetation-diagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows,indent=2))
