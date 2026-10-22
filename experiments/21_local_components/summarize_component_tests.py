"""Aggregate frozen-test evidence without refitting or weakening original criteria."""
import hashlib,json
import numpy as np
from scene import ROOT
freeze=json.loads((ROOT/'results/component-test-prediction-freeze.json').read_text())
for p,h in freeze['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
reports=[]
for name in freeze['cases']:
 p=ROOT/'results'/f'{name}-test.json';assert p.exists(),f'Await test evaluation: {name}'
 proof=json.loads((ROOT/'results'/f'{name}-collected.json').read_text());assert not any(proof['cleanup'].values()) and proof['checkpoint_files_verified']>0
 r=json.loads(p.read_text());assert r['full_horizon'],'Incomplete tests must be interpreted separately';reports.append(r)
models={}
for label in ['graph','baseline','ablation']:
 rows=[]
 for r in reports:
  x=next(m for m in r['models'] if m['model']==label);metric=x['metrics'];base=next(m for m in r['models'] if m['model']=='baseline')['metrics']['absolute_dose_MAE_all_kj_m2']
  rows.append(dict(case=r['case'],classification_correct=metric['classification_correct'],reference_ignition=r['whole_structure_ignition'],predicted_ignition=metric['predicted_ignition'],ignition_time_reference_s=metric['reference_whole_structure_first_burning_s'],ignition_time_prediction_s=metric['predicted_ignition_s'],temperature_MAE_C=metric['temperature_MAE_all_C'],exposed_surfaces=metric['exposed_surface_count'],median_exposed_dose_error=metric['median_exposed_normalized_dose_error'],p90_exposed_dose_error=metric['p90_exposed_normalized_dose_error'],dose_MAE_kj_m2=metric['absolute_dose_MAE_all_kj_m2'],dose_MAE_improvement_over_additive=1-metric['absolute_dose_MAE_all_kj_m2']/base if base else None,canopies=x['canopies']))
 models[label]=rows
positives=sum(r['whole_structure_ignition'] for r in reports)
out=dict(frozen_utc=freeze['frozen_utc'],models=models,test_cases=len(reports),positive_cases=positives,negative_cases=len(reports)-positives,original_coverage_criterion='NOT SATISFIED:2 scenes/90s rather than16 scenes/180s, with at least4 positive and4 negative required; do not call2/2 labels a validation pass.',speed=json.loads((ROOT/'results/frozen-component-speed-breakdown.json').read_text()),reservations_usd=json.loads((ROOT/'budget-overnight.json').read_text())['reserved_usd'],scientific_scope='Fixed0.5m FDS-reference composition test, not physical validation. Recorded Sonoma footprints with assigned flat heights and synthetic10/16m canopy locations; generic vegetation/20mm wood; artificial20s ignition; no trunks/groundcover/embers. Canopy power state is fuel-release rate times heat of combustion, not measured gas-phase HRR. Report canopy failure even if building label is correct.')
(ROOT/'results/component-test-summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(cases=len(reports),positives=positives,models=models),indent=2))
