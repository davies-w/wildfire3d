"""Post-hoc strength strata; derived from existing full-history metrics, no fitting."""
import json,statistics
from pathlib import Path
R=Path(__file__).parent
source=json.loads((R/'results/coverage-summary.json').read_text())
keys=['HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','truth_hot_temperature_relative_L1_percent','truth_mean_HRR_kW','predicted_mean_HRR_kW','temperature_MAE_C']
rows=[]
for arm in ['continue120','expand360']:
 for cohort in ['all_train360','validation32']:
  for low,high in [(0,1),(1,10),(10,100),(100,None)]:
   group=[x['metrics'] for x in source['configuration_metrics'] if x['arm']==arm and x['stage']=='final' and x['cohort']==cohort and x['window']=='post_source' and low<=x['metrics']['truth_mean_HRR_kW'] and (high is None or x['metrics']['truth_mean_HRR_kW']<high)]
   rows.append(dict(arm=arm,cohort=cohort,truth_mean_HRR_kW_range=[low,high],count=len(group),median={k:statistics.median(x[k] for x in group if x[k] is not None) if group else None for k in keys}))
(R/'results/strength-diagnosis.json').write_text(json.dumps(dict(scope='Post-hoc diagnostic strata, not a new test or a training objective. Configurations weighted equally after seed averaging. Medians of truth and predictions are separate distributions, not paired ratios.',rows=rows),indent=2)+'\n')
