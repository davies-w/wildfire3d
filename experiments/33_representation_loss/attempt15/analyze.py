"""Matched loss comparison: same initial model/optimizer/schedule; no independent test."""
import json,statistics
from pathlib import Path
R=Path(__file__).parent
report=json.loads((R/'data/collected/report.json').read_text());rows=report['rows'];arms=['control','strength_low','strength_high']
checks=[json.loads((R/f'data/collected/{a}-resume-check.json').read_text()) for a in arms]
assert len({x['initial_weights_sha256'] for x in checks})==1 and len({x['initial_optimizer_sha256'] for x in checks})==1
initial={a:{x['case']:x for x in rows if x['arm']==a and x['stage']=='initial'} for a in arms};assert all(len(v)==88 for v in initial.values())
for c in initial['control']:
 for a in arms[1:]:
  for w in ['all','post_source','late']:assert initial[a][c][w]==initial['control'][c][w]
keys=['truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','temperature_rise_relative_L1_percent','flame_IoU','velocity_vector_relative_L1_percent','temperature_MAE_C','truth_mean_HRR_kW','predicted_mean_HRR_kW'];out={'initial_equal':True,'scope':report['scope'],'summary':[],'configurations':[],'seed_spread':[]}
for a in arms:
 for stage in ['initial','final']:
  for split in ['train','validation']:
   rr=[x for x in rows if (x['arm'],x['stage'],x['split'])==(a,stage,split)]
   for w in ['all','post_source','late']:
    grouped=[]
    for n in sorted({x['configuration'] for x in rr}):
     ss=[x for x in rr if x['configuration']==n];vv={k:[x[w][k] for x in ss if x[w][k] is not None] for k in keys};m={k:statistics.mean(v) if v else None for k,v in vv.items()};grouped.append(m);out['configurations'].append(dict(arm=a,stage=stage,split=split,window=w,configuration=n,metrics=m))
     if len(ss)>1:out['seed_spread'].append(dict(arm=a,stage=stage,window=w,configuration=n,range={k:max(v)-min(v) if v else None for k,v in vv.items()}))
    for lo,hi in [(0,None),(0,1),(1,10),(10,100),(100,None)]:
     gg=[m for m in grouped if lo<=m['truth_mean_HRR_kW'] and (hi is None or m['truth_mean_HRR_kW']<hi)];v={k:[m[k] for m in gg if m[k] is not None] for k in keys}
     out['summary'].append(dict(arm=a,stage=stage,split=split,window=w,strength_range=[lo,hi],count=len(gg),median={k:statistics.median(x) if x else None for k,x in v.items()},mean={k:statistics.mean(x) if x else None for k,x in v.items()}))
(R/'results/comparison.json').write_text(json.dumps(out,indent=2)+'\n')
for x in out['summary']:
 if x['stage']=='final' and x['window']=='post_source' and x['strength_range']==[0,None]:print(x['arm'],x['split'],x['median'])
