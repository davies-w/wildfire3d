"""Compare training coverage at equal optimizer updates, balanced by configuration."""
import json,statistics
from pathlib import Path
R=Path(__file__).parent

def analyze(report,plan,checks):
 rows=report['rows'];arms=['pilot12','expanded120'];pilot=set(plan['pilot_configurations'])
 assert report['optimizer_isolation_verified']
 assert len({x['initial_weights_sha256'] for x in checks})==1
 assert len({x['initial_optimizer_sha256'] for x in checks})==1
 initial={a:{x['case']:x for x in rows if x['arm']==a and x['stage']=='initial'} for a in arms}
 assert len(initial['pilot12'])==160
 for c,x in initial['pilot12'].items():
  for w in ['all','post_source','late']:assert x[w]==initial['expanded120'][c][w],(c,w)
 keys=['truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','temperature_rise_relative_L1_percent','flame_IoU','velocity_vector_relative_L1_percent','temperature_MAE_C','truth_mean_HRR_kW','predicted_mean_HRR_kW']
 result={'scope':'Equal6000updates, fixedloss/current6000initialstate; coverage12vs120, not equalepochs. Previously used development validation, not pristine test. Seed metrics averaged within configuration before mean/median.','initial_weights_optimizer_metrics_equal':True,'summary':[],'configuration_metrics':[],'paired':[],'seed_spread':[],'weak_cases':[]}
 for arm in arms:
  for stage in ['initial','final']:
   for cohort in ['pilot_train12','additional_train108','all_train120','validation32']:
    rr=[x for x in rows if (x['arm'],x['stage'])==(arm,stage) and ((cohort=='validation32' and x['split']=='validation') or (cohort!='validation32' and x['split']=='train' and (cohort=='all_train120' or ((x['configuration'] in pilot)==(cohort=='pilot_train12')))))]
    names=sorted({x['configuration'] for x in rr});assert len(names)=={'pilot_train12':12,'additional_train108':108,'all_train120':120,'validation32':32}[cohort]
    for window in ['all','post_source','late']:
     metrics=[]
     for name in names:
      ss=[x for x in rr if x['configuration']==name];vv={k:[x[window][k] for x in ss if x[window][k] is not None] for k in keys};m={k:statistics.mean(v) if v else None for k,v in vv.items()};metrics.append(m)
      result['configuration_metrics'].append(dict(arm=arm,stage=stage,cohort=cohort,window=window,configuration=name,seeds=len(ss),metrics=m))
      if len(ss)>1 and stage=='final':result['seed_spread'].append(dict(arm=arm,window=window,configuration=name,range={k:max(v)-min(v) if v else None for k,v in vv.items()}))
     vv={k:[m[k] for m in metrics if m[k] is not None] for k in keys};result['summary'].append(dict(arm=arm,stage=stage,cohort=cohort,window=window,configurations=len(names),trajectories=len(rr),median={k:statistics.median(v) if v else None for k,v in vv.items()},mean={k:statistics.mean(v) if v else None for k,v in vv.items()},defined={k:len(v) for k,v in vv.items()}))
     if stage=='final' and window=='post_source':result['weak_cases'] += [dict(arm=arm,cohort=cohort,configuration=n,metrics=m) for n,m in sorted(zip(names,metrics),key=lambda nm:nm[1]['truth_mean_HRR_kW'])[:3]]
 for x in result['configuration_metrics']:
  if x['arm']!='expanded120' or x['stage']!='final':continue
  base=next(y for y in result['configuration_metrics'] if y['arm']=='pilot12' and all(y[k]==x[k] for k in ['stage','cohort','window','configuration']))
  result['paired'].append(dict(cohort=x['cohort'],window=x['window'],configuration=x['configuration'],delta_expanded_minus_pilot={k:x['metrics'][k]-base['metrics'][k] if x['metrics'][k] is not None and base['metrics'][k] is not None else None for k in keys}))
 return result

if __name__=='__main__':
 report=json.loads((R/'data/collected/report.json').read_text());plan=json.loads((R/'coverage-plan.json').read_text());checks=[json.loads((R/f'data/collected/{a}-resume-check.json').read_text()) for a in ['pilot12','expanded120']]
 result=analyze(report,plan,checks);(R/'results/coverage-summary.json').write_text(json.dumps(result,indent=2)+'\n')
 for x in result['summary']:
  if x['stage']=='final' and x['window']=='post_source':print(x['arm'],x['cohort'],x['median'])
