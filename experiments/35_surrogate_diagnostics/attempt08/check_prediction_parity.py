"""Compare CPU viewer counts with original final GPU evaluation on shared cases."""
from pathlib import Path
import json,subprocess,numpy as np
R=Path(__file__).parent;g='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';dest=R/'data/gpu-counts';dest.mkdir(exist_ok=True)
report=json.loads((R/'data/training-report.json').read_text());audit=json.loads((R/'results/prediction-audit.json').read_text());ids={n:i for i,n in enumerate(audit['cases'])};rows=[]
for model,local in zip(report['models'],audit['models']):
 name=f"time-{model['frame']:03}-epoch-{model['epochs']:03}-counts.npz";p=dest/name
 if not p.exists():subprocess.run([g,'storage','cp','gs://tmrw-wildfire-20261015-trial/diagnostics35/attempt07/'+name,str(p)],check=True)
 z=np.load(p);cpu=np.array([local['counts'][ids[str(n)]] for n in z['case']]);gpu=z['counts'][:,:4];diff=cpu-gpu
 rows.append(dict(time_s=model['nominal_time_s'],shared_cases=len(cpu),cases_with_count_difference=int(np.any(diff!=0,axis=1).sum()),maximum_count_difference=int(abs(diff).max()),sum_absolute_count_difference=int(abs(diff).sum())))
(R/'results/cpu-gpu-parity.json').write_text(json.dumps(dict(models=rows,scope='Counts compared on400 original cases; equal counts do not prove identical spatial masks. CPU/GPU float rounding may change near-zero decisions.'),indent=2));print(rows)
