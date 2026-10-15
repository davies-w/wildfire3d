"""Compare identical input decks across laptop and cloud; neither is ground truth."""
import json
import numpy as np
from study import ROOT,read_csv,save

results=[]
for p in sorted((ROOT/'data/cloud').glob('*/result.json')):
    cloud=json.loads(p.read_text());name=cloud['case']
    local_dir=ROOT/'data/local'/p.parent.name
    local=json.loads((local_dir/'result.json').read_text())
    if cloud['deck_sha256']!=local['deck_sha256']:raise ValueError('Different decks: '+name)
    if not cloud['full_horizon'] or cloud['returncode']:raise ValueError('Incomplete: '+name)
    a=read_csv(p.parent/f'{name}_devc.csv');b=read_csv(local_dir/f'{name}_devc.csv')
    times=np.array([r['Time'] for r in b if r['Time']>=max(a[0]['Time'],b[0]['Time']) and r['Time']<=min(a[-1]['Time'],b[-1]['Time'])])
    metrics={}
    for key in b[0]:
        if key=='Time':continue
        x=np.interp(times,[r['Time'] for r in a],[r[key] for r in a]);y=np.interp(times,[r['Time'] for r in b],[r[key] for r in b])
        metrics[key]={'max_abs_difference':float(np.max(abs(x-y))),'rmse':float(np.sqrt(np.mean((x-y)**2)))}
    results.append({'case':name,'cloud_wall_s':cloud['wall_seconds'],'local_wall_s':local['wall_seconds'],'local_over_cloud':local['wall_seconds']/cloud['wall_seconds'],'cloud_steps':cloud['steps'],'local_steps':local['steps'],'metrics':metrics})
if len(results)!=4:raise ValueError('Expected four complete cloud cases')
save(ROOT/'results/cloud-comparison.json',{'comparisons':results,'caveat':'Different hardware, compiler, OS, and local contention. Transient LES differences are not physical validation.'})
print(json.dumps(results,indent=2))
