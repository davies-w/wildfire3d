import json
from pathlib import Path
import numpy as np
R=Path(__file__).parent
for name in ['capacity','physical','factorized']:
 p=R/f'results/{name}.json'
 if not p.exists():continue
 r=json.loads(p.read_text());scores={}
 for key in ['baseline','final']:
  a=r[key]['rows'];scores[key]=dict(late_mean_kW=float(np.mean([v['heat_kW'] for v in a if v['time_s']>=119])),late_truth_kW=float(np.mean([v['truth_heat_kW'] for v in a if v['time_s']>=119])),hot_MAE_C=float(np.mean([v['hot_MAE_C'] for v in a])),radiation_relative_L1=float(np.mean([v['radiation_relative_L1'] for v in a])),peak_MAE_C=float(np.mean([abs(v['peak_C']-v['truth_peak_C']) for v in a])))
 b=scores['baseline'];f=scores['final'];gates=dict(late=f['late_mean_kW']<=.1*b['late_mean_kW'],hot=f['hot_MAE_C']<=1.1*b['hot_MAE_C'],radiation=f['radiation_relative_L1']<=b['radiation_relative_L1'],peak=f['peak_MAE_C']<=b['peak_MAE_C']);scores.update(gates=gates,pass_all=all(gates.values()),evaluation='training reconstruction only' if name=='capacity' else 'validation')
 (R/f'results/{name}-screen.json').write_text(json.dumps(scores,indent=2));print(name,json.dumps(scores,indent=2))
