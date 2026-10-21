from pathlib import Path
import json,numpy as np
R=Path(__file__).parent
keys=['hot_MAE_C','HRR_curve_relative_L1','radiation_dose_relative_L1','peak_error_C','velocity_MAE_m_s','flame_IoU']
def mean(rows):return {k:float(np.mean([r['post_source'][k] for r in rows])) for k in keys}
def main():
 d=json.loads((R/'results/learning.json').read_text());f=json.loads((R/'results/fresh-test-evaluation.json').read_text());groups={}
 for split in ['train','validation']:
  for new in [False,True]:
   for model in ['snapshot','hybrid','state_reset_ablation']:
    rows=[r for r in d['rows'] if r['split']==split and r['new_geometry']==new and r['model']==model]
    if rows:groups[f'{split}_{"new" if new else "original"}_{model}']=dict(configurations=len(rows),**mean(rows))
 for model in ['snapshot','hybrid','state_reset_ablation']:groups['fresh_test_'+model]=dict(configurations=2,**mean([r for r in f['rows'] if r['model']==model]))
 # Pointwise fresh outcomes are reported, not hidden by the two-case average.
 report=dict(development_and_test_metrics=groups,snapshot_selected_step=d['snapshot_training']['selected_step'],hybrid_selected_step=d['hybrid_training']['selected_step'],inference_median_s=d['inference_median_s'],budget_reservations_usd=json.loads((R/'budget.json').read_text())['reserved_usd'],caution='Exploratory two-case fresh test, same generic cone family; no real-world validation. Hybrid uses snapshot prior at every time. No embers.')
 (R/'results/summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
