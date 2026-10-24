"""Audit existing material surface temperature and spatial summaries; no optimization."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent/'attempt12';base=np.load(R.parent/'attempt18/data/sequences.npz');schema=json.loads((R.parent/'attempt18/schema.json').read_text());items=json.loads((P/'inventory.json').read_text());heat=[];spatial=[];records=[]
for i,it in enumerate(items):
 n=it['conditions']['case'];p=P/'data/states'/f'{n}.json';d=json.loads(p.read_text());hh=[];ss=[];mass0=d['snapshots'][0]['remaining_total_material_mass_kg']
 for row in d['snapshots']:
  classes=row['material_classes'];m=np.array([c['remaining_total_mass_kg'] for c in classes]);temp=np.array([c['mass_weighted'].get('PARTICLE TEMPERATURE') if c['mass_weighted'].get('PARTICLE TEMPERATURE') is not None else 20 for c in classes]);assert (m>=0).all() and np.isfinite(temp).all()
  # Fixed initial mass denominator: no disappearing-mass mean amplification; units Kelvin, not joules.
  hh.append(float(np.sum(m*(temp-20))/mass0))
  plume=row['hot_plume'];ss.append([row['temperature_excess_integral_K_m3'],*(plume['centroid_m'] if plume else [0,0,0]),float(plume is not None)])
 h=np.array(hh);assert len(h)==91;assert np.allclose([r['time_s'] for r in d['snapshots']],base['time'][i]);heat.append(h);spatial.append(ss)
 records.append(dict(case=n,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),initial_mass_kg=mass0,initial_proxy_K=float(h[0]),peak_proxy_K=float(h.max()),final_proxy_K=float(h[-1]),particle_units=d['particle_quantities'][0]))
heat=np.array(heat);spatial=np.array(spatial);assert heat.shape==(520,91)
np.savez_compressed(R/'data/thermal_candidates.npz',thermal=heat.astype('float32'),spatial=spatial.astype('float32'),time=base['time'])
summary=dict(histories=520,configurations=480,thermal_proxy='Sum remaining particle mass * (particle surface temperature C -20C), divided by initial total particle mass. Kelvin-equivalent surface-heating index; NOT stored energy.',no_true_stored_energy='No internal temperature profile or per-frame component heat capacity/composition in saved summaries. Surface TMP_F is not volume-mean material temperature. Gas density/composition also absent.',thermal_range_K=[float(heat.min()),float(heat.max())],initial_range_K=[float(heat[:,0].min()),float(heat[:,0].max())],peak_quantiles_K=np.quantile(heat.max(1),[0,.25,.5,.75,1]).tolist(),spatial_presence_fraction=float(spatial[:,:,-1].mean()),spatial_candidate='Gas temperature-excess centroid with separate strength/presence; source-inclusive and not directional heat transfer. Not crown-anchored; cannot replace an energy scalar.',stage3_rule='First evaluate scalar controlled comparison. Audit spatial candidate interpretation now; only train spatial extension if validation evidence shows scalar insufficient and identifiable spatial candidate with reproducible labels. Do not select additions from test results.',records=records)
(R/'results/audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
