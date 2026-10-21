"""Configuration-balanced reporting without concealing weak-burning failures or seed repeats."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).parent
KEYS=['temperature_rise_relative_L1_percent','truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','peak_temperature_rise_error_percent','velocity_vector_relative_L1_percent','flame_IoU']
def aggregate(rows,metadata):
 out={}
 for model in sorted({r['model'] for r in rows}):
  out[model]={}
  for window in ['all','post_source','late']:
   out[model][window]={}
   for key in KEYS:
    grouped={}
    for r in rows:
     if r['model']!=model:continue
     v=r[window][key]
     if v is not None:grouped.setdefault(metadata[r['case']]['configuration'],[]).append(v)
    vals=[float(np.mean(v)) for v in grouped.values()]
    out[model][window][key]=dict(mean=float(np.mean(vals)),median=float(np.median(vals)),configurations=len(vals)) if vals else None
 return out

def main():
 learning=json.loads((R/'results/learning.json').read_text());test=json.loads((R/'results/fresh-test-evaluation.json').read_text());meta={c['case']:c for c in json.loads((R/'development.json').read_text())+json.loads((R/'fresh-tests.json').read_text())};budget=json.loads((R/'budget.json').read_text());assert json.loads((R/'results/evaluation-collected.json').read_text())['complete'];assert len({c['configuration'] for c in meta.values() if c['split']=='test'})==40
 splits={}
 for split in ['train','validation']:
  for new in [True,False]:
   rows=[r for r in learning['rows'] if meta[r['case']]['split']==split and meta[r['case']]['new_geometry']==new];splits[split+('_new' if new else '_legacy')]=aggregate(rows,meta)
 weaknesses=[]
 for model in ['snapshot','hybrid']:
  rows=[r for r in learning['rows'] if r['model']==model and r['split']=='train'];worst=sorted(rows,key=lambda r:abs(r['post_source']['predicted_mean_HRR_kW']-r['post_source']['truth_mean_HRR_kW']),reverse=True)[:10]
  weaknesses.extend(dict(case=r['case'],configuration=meta[r['case']]['configuration'],model=model,truth_mean_HRR_kW=r['post_source']['truth_mean_HRR_kW'],predicted_mean_HRR_kW=r['post_source']['predicted_mean_HRR_kW'],HRR_error_percent=r['post_source']['HRR_curve_relative_L1_percent']) for r in worst)
  # Explicitly retain the previously documented weak-burning training failure.
  weaknesses.extend(dict(case=r['case'],model=model,prior_weak_case=True,post_source=r['post_source']) for r in rows if r['case']=='v31_09')
 result=dict(development=splits,fresh_test=aggregate(test['rows'],meta),training_failures=weaknesses,seed_ensembles=test['seed_ensembles'],inference_median_seconds=learning['inference_median_s'],snapshot_training=learning['snapshot_training'],hybrid_training=learning['hybrid_training'],budget=dict(cap_usd=budget['authorized_usd'],reserved_usd=budget['reserved_usd'],invoice_spend=None,meaning='Reservations retained including failed attempts; not billed spend'),scope='Single fixed generic cone family, six gas fields, .5m outputs; hybrid material state2m; no solid ground temperature, embers or multi-tree composition',percentages='Errors relative to corresponding FDS quantities; percentages can greatly exceed100 for weak reference burning. Null denominators remain missing, never counted as zero. Average seeds within configurations before averaging configurations.',projection_cases=test['projections'],fresh_configurations=test['fresh_configurations'],fresh_trajectories=test['fresh_trajectories'])
 (R/'results/final-summary.json').write_text(json.dumps(result,indent=2));print('Final summary written; inspect training failures and seed spread alongside aggregate errors.')
if __name__=='__main__':main()
