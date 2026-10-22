"""Configuration-paired full-history development comparison; no model fitting."""
import json,statistics
from pathlib import Path
R=Path(__file__).parent
report=json.loads((R/'data/collected/report.json').read_text());rows=report['rows'];arms=['control','dose','dose_background'];keys=['truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','temperature_rise_relative_L1_percent','flame_IoU','minimum_C','velocity_vector_relative_L1_percent']
checks=[json.loads((R/f'data/collected/{a}-resume-check.json').read_text()) for a in arms];assert all(x['passed'] for x in checks);assert len({x['initial_weights_sha256'] for x in checks})==1
initial={a:{x['case']:x for x in rows if x['arm']==a and x['stage']=='initial'} for a in arms}
for c,x in initial['control'].items():
 for a in arms:
  for w in ['all','post_source','late']:assert x[w]==initial[a][c][w],(a,c,w)
out={'initial_weights_and_metrics_identical':True,'scope':'12 strength-stratified training / 8 development-validation configurations, not pristine or IID test. All trajectory windows retained. Percent metrics can be unstable for weak truth.','summary':[],'paired':[],'weak_cases':[]}
for split in ['train','validation']:
 for a in arms:
  for stage in ['initial','final']:
   rr=[x for x in rows if (x['split'],x['arm'],x['stage'])==(split,a,stage)]
   for w in ['all','post_source','late']:
    vals={k:[x[w][k] for x in rr if x[w][k] is not None] for k in keys}
    out['summary'].append(dict(split=split,arm=a,stage=stage,window=w,median={k:statistics.median(v) if v else None for k,v in vals.items()},defined={k:len(v) for k,v in vals.items()}))
  final={x['case']:x for x in rows if (x['split'],x['arm'],x['stage'])==(split,a,'final')}
  ctrl={x['case']:x for x in rows if (x['split'],x['arm'],x['stage'])==(split,'control','final')}
  for c,x in final.items():
   out['paired'].append(dict(split=split,arm=a,case=c,post_source_delta_vs_control={k:x['post_source'][k]-ctrl[c]['post_source'][k] if x['post_source'][k] is not None and ctrl[c]['post_source'][k] is not None else None for k in keys}))
  weak=sorted(final,key=lambda c:final[c]['post_source']['truth_mean_HRR_kW'])[:3]
  out['weak_cases'] += [dict(split=split,arm=a,case=c,**final[c]['post_source']) for c in weak]
(R/'results/matched-summary.json').write_text(json.dumps(out,indent=2)+'\n')
for x in out['summary']:
 if x['window']=='post_source' and x['stage']=='final':print(x['split'],x['arm'],{k:round(v,2) if v is not None else None for k,v in x['median'].items()})
