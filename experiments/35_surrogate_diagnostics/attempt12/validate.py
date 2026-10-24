"""Require full coverage and validate compact state contracts before any folds/training."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
items=json.loads((R/'inventory.json').read_text());groups={};records=[]
for it in items:
 c=it['conditions'];n=c['case'];p=R/'data/states'/(n+'.json');x=json.loads(p.read_text());rs=x['snapshots'];t=np.array([r['time_s'] for r in rs]);assert len(t)>1 and np.all(np.diff(t)>0) and t[-1]>=179.9
 for r in rs:
  assert r['alignment_error_s']<.21 and len(r['material_classes'])==4
  assert abs(sum(v['remaining_total_mass_kg'] for v in r['material_classes'])-r['remaining_total_material_mass_kg'])<1e-5
  assert (r['hot_plume'] is None)==(r['hot_volume_m3']==0)
  for key in ['hot_plume','hrr_region']:
   m=r[key]
   if m:
    cov=np.array(m['covariance_m2']);assert np.isfinite(cov).all() and np.linalg.eigvalsh(cov).min()>-1e-7
    assert np.all(np.array(m['centroid_m'])>=0) and np.all(np.array(m['centroid_m'])<=[24,16,16])
  assert np.isfinite([r[k] for k in ['gas_HRR_kW','global_HRR_kW','solid_oxidation_HRR_kW','fuel_vapor_release_kg_s','remaining_total_material_mass_kg']]).all()
 for labels in x['particle_quantities']:
  assert len(labels)==6 and labels[0]['unit']=='C' and labels[1]['unit']=='kg' and labels[4]['unit']=='kW/m2'
 key=tuple(round(float(v),8) for v in [c.get('crown_height_m',8),c['moisture'],c.get('loading_multiplier',1),c['wind_speed'],c['angle_deg']]);groups.setdefault(key,[]).append(n)
 records.append(dict(case=n,source=it['source'],snapshots=len(t),transitions=len(t)-1,first_s=float(t[0]),last_s=float(t[-1])))
assert len(records)==520 and len(groups)==480
proof=dict(passed=True,histories=len(records),configurations=len(groups),snapshots=sum(r['snapshots'] for r in records),transitions=sum(r['transitions'] for r in records),exclusions=[],records=records,checks=['complete 520 archive coverage','actual increasing timestamps and 180s horizon','particle alignment','four material classes and mass sums','six particle quantities and units','finite PSD plume moments','physical configuration grouping'],scope='Schema compatibility, not proof of compact-state sufficiency or physical validation. Legacy geometries retained and labeled.')
(R/'results/validation.json').write_text(json.dumps(proof,indent=2));print({k:v for k,v in proof.items() if k!='records'})
