import json
from pathlib import Path
import numpy as np
R=Path(__file__).parent;r=json.loads((R/'results/test-summary.json').read_text());summary={}
for name in ['original','physical','interpolation']:
 rows=[r for r in r['rows'] if r['model']==name];summary[name]={}
 for window in ['all','post_source','late']:
  summary[name][window]={k:float(np.mean([row[window][k] for row in rows])) for k in ['hot_MAE_C','HRR_curve_relative_L1','radiation_dose_relative_L1','truth_mean_HRR_kW','predicted_mean_HRR_kW','velocity_vector_MAE_m_s']}
  summary[name][window]['peak_error_C']=float(np.mean([abs(row[window]['predicted_peak_C']-row[window]['truth_peak_C']) for row in rows]))
  iou=[row[window]['flame_proxy_IoU'] for row in rows if row[window]['flame_proxy_IoU'] is not None];summary[name][window]['flame_proxy_IoU']=float(np.mean(iou)) if iou else None
(R/'results/aggregate.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
