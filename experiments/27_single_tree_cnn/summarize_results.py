"""Compact report derived from preserved per-case metrics, without selecting tests."""
import json
from pathlib import Path
import numpy as np
R=Path(__file__).parent
rows=json.loads((R/'results/test-summary.json').read_text())['cases']
keys=['hot_union_temperature_MAE_C','flame_proxy_IoU','hot_union_velocity_error_m_s','excess_radiation_dose_relative_L1','integrated_HRR_dose_relative_error']
summary={}
for model in ['cnn_8','cnn_16','cnn_32','interpolation_8','interpolation_16','interpolation_32']:
 a=[r for r in rows if r['model']==model]
 summary[model]={section:{k:dict(mean=float(np.mean([r[k] for r in a])) if section=='all_times' else float(np.mean([r[section][k] for r in a])),per_case=[r[k] if section=='all_times' else r[section][k] for r in a]) for k in keys} for section in ['all_times','post_source','ten_second_smoothed']}
wins={k:sum(next(r for r in rows if r['case']==c and r['model']=='cnn_32')[k] < next(r for r in rows if r['case']==c and r['model']=='interpolation_32')[k] for c in sorted({r['case'] for r in rows})) for k in keys if k!='flame_proxy_IoU'}
summary['CNN32_lower_error_than_interpolation32_count_of_6']=wins
summary['averaging']='Equal weight per held-out configuration, not per cell across pooled cases. Six cases; no claim of broad population accuracy.'
(R/'results/compact-summary.json').write_text(json.dumps(summary,indent=2))
for name,a in summary.items():
 if isinstance(a,dict) and 'all_times' in a:print(name,{k:round(v['mean'],4) for k,v in a['all_times'].items()})
print(wins)
