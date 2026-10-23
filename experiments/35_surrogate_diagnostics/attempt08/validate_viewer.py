"""Validate all exported sparse masks, case coverage, metrics and model times."""
from pathlib import Path
import json,base64,numpy as np
R=Path(__file__).parent;idx=json.loads((R/'data/viewer/index.json').read_text());assert idx['times']==list(range(0,181,20));assert len(idx['cases'])==472
count=0
for c in idx['cases']:
 row=json.loads((R/'data/viewer/cases'/(c['case']+'.json')).read_text());assert set(row['frames'])==set(map(str,idx['times']))
 for t,f in row['frames'].items():
  a=np.frombuffer(base64.b64decode(f['truth']),dtype='<u2');b=np.frombuffer(base64.b64decode(f['prediction']),dtype='<u2');assert len(a)==len(set(a.tolist())) and len(b)==len(set(b.tolist()));assert all(v<49152 for v in [a.max(initial=0),b.max(initial=0)])
  tp=len(np.intersect1d(a,b));m=f['metrics'];assert m['tp']==tp and m['fp']==len(b)-tp and m['fn']==len(a)-tp and m['tn']==49152-len(np.union1d(a,b));count+=1
(R/'results/viewer-validation.json').write_text(json.dumps(dict(cases=len(idx['cases']),snapshots=count,passed=True,checks=['ten times per case','sparse mask unique indices in grid','all confusion counts recomputed from exported masks']),indent=2));print('Validated',count,'snapshots')
