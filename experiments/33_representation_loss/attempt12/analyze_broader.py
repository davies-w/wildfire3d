"""Configuration-balanced frozen-model evaluation, separating tuning-panel cases."""
from pathlib import Path
import json,statistics
R=Path(__file__).parent
r=json.loads((R/'data/collected/report.json').read_text());rows=r['rows'];pilot={x['configuration'] for x in json.loads((R/'pilot-cases.json').read_text()) if x['split']=='validation'}
keys=['truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','temperature_rise_relative_L1_percent','flame_IoU','velocity_vector_relative_L1_percent','temperature_MAE_C','truth_mean_HRR_kW','predicted_mean_HRR_kW']
result={'scope':'Frozen evaluation on existing development data, not pristine test. Seed metrics averaged within configuration before reporting mean/median. Null undefined percentages excluded with counts.','summary':[],'configuration_metrics':[],'seed_spread':[]}
for arm in sorted({x['arm'] for x in rows}):
 for cohort in ['training12','validation32','pilot8','additional24']:
  rr=[x for x in rows if x['arm']==arm and ((cohort=='training12' and x['split']=='train') or (cohort!='training12' and x['split']=='validation' and (cohort=='validation32' or ((x['configuration'] in pilot)==(cohort=='pilot8')))))]
  names=sorted({x['configuration'] for x in rr});assert len(names)=={'training12':12,'validation32':32,'pilot8':8,'additional24':24}[cohort]
  for window in ['all','post_source','late']:
   configs=[]
   for name in names:
    ss=[x for x in rr if x['configuration']==name];vals={k:[x[window][k] for x in ss if x[window][k] is not None] for k in keys};metrics={k:statistics.mean(v) if v else None for k,v in vals.items()};configs.append(metrics)
    result['configuration_metrics'].append(dict(arm=arm,cohort=cohort,configuration=name,window=window,seeds=len(ss),metrics=metrics))
    if len(ss)>1 and cohort=='validation32':result['seed_spread'].append(dict(arm=arm,configuration=name,window=window,range={k:max(v)-min(v) if v else None for k,v in vals.items()}))
   vv={k:[c[k] for c in configs if c[k] is not None] for k in keys}
   result['summary'].append(dict(arm=arm,cohort=cohort,window=window,configurations=len(names),trajectories=len(rr),median={k:statistics.median(v) if v else None for k,v in vv.items()},mean={k:statistics.mean(v) if v else None for k,v in vv.items()},defined={k:len(v) for k,v in vv.items()},median_inference_s=statistics.median(x['inference_s'] for x in rr)))
(R/'results/broader-summary.json').write_text(json.dumps(result,indent=2)+'\n')
for x in result['summary']:
 if x['window']=='post_source' and x['cohort'] in ['validation32','additional24']:print(x['arm'],x['cohort'],x['median'])
