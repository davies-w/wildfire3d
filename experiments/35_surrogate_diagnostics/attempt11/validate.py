from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;paths=sorted((R/'data/states').glob('x*.json'));assert len(paths)==48
count=0
for p in paths:
 x=json.loads(p.read_text());rs=x['snapshots'];assert len(rs)==91 and np.all(np.diff([r['time_s'] for r in rs])>0)
 for r in rs:
  assert r['alignment_error_s']<.21 and len(r['material_classes'])==4
  assert abs(sum(c['remaining_total_mass_kg'] for c in r['material_classes'])-r['remaining_total_material_mass_kg'])<1e-5
  assert (r['hot_plume'] is None)==(r['hot_volume_m3']==0)
  for key in ['hot_plume','hrr_region']:
   m=r[key]
   if m:
    cov=np.array(m['covariance_m2']);assert np.isfinite(cov).all() and np.linalg.eigvalsh(cov).min()>-1e-8
    c=np.array(m['centroid_m']);assert np.all(c>=0) and np.all(c<=[24,16,16])
  count+=1
 for q in x['particle_quantities']:
  assert len(q)==6 and q[0]['unit']=='C' and q[1]['unit']=='kg' and q[4]['unit']=='kW/m2'
(R/'results/validation.json').write_text(json.dumps(dict(passed=True,cases=len(paths),snapshots=count,checks=['strict timestamps','particle alignment','class mass sums','inactive shape masks','finite positive-semidefinite moments','centroids inside domain','raw particle units'],scope='Structural/numeric validation, not proof that compact state is sufficient for prediction.'),indent=2))
