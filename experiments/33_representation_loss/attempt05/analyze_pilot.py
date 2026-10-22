import json,statistics
from pathlib import Path
R=Path(__file__).parent
r=json.loads((R/'results/report.json').read_text());out=[]
keys=['truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','temperature_rise_relative_L1_percent','flame_IoU']
for split in ['train','validation']:
 for arm in ['current','loss_only','spatial_heads']:
  for stage in ['initial','final']:
   rows=[x['post_source'] for x in r['rows'] if (x['arm'],x['stage'],x['split'])==(arm,stage,split)]
   out.append(dict(split=split,arm=arm,stage=stage,median={k:statistics.median(x[k] for x in rows if x[k] is not None) for k in keys}))
(R/'results/summary.json').write_text(json.dumps(out,indent=2))
