from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent
checks=[]
for case in ['tree51_001323_baseline','tree51_001336_baseline']:
 root=R/'data/cone-comparison-preview'/case;base=np.load(R/'data/training-preview'/case/'training.npz')
 for kind,n in [('cone',11),('free_cone',14)]:
  p=root/kind;d=np.load(p/'training.npz');x=d['state'];assert x.shape==(91,n) and np.isfinite(x).all();assert np.array_equal(x[:,:4],base['state'][:,:4]);assert d['observed'].sum()==6 and d['interpolated'].sum()==85
  for j,t in enumerate(d['source_time_s']):assert np.array_equal(x[np.flatnonzero(d['time_s']==t)[0],4:],d['source_spatial_state'][j])
  assert (d['right_weight']>=0).all() and (d['right_weight']<=1).all()
  for row in x[:,4:]:
   if not row[0]:assert (row==0).all()
   else:assert abs(np.linalg.norm(row[1:4] if kind=='cone' else row[4:7])-1)<1e-12
  s=json.loads((p/'first-transition.json').read_text());assert np.array_equal(s['initial_state']['values'],x[0]) and np.array_equal(s['next_state']['values'],x[1]);assert s['no_hidden_history_window']
  checks.append({'case':case,'variant':kind,'rows':91,'channels':n,'observed':6,'interpolated':85})
 assert Image.open(root/'comparison-3d.gif').n_frames==91
 v=json.loads((root/'animation-verification.json').read_text());assert np.array_equal(v['time_s'],base['time_s'])
(R/'data/cone-comparison-preview/validation.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2)+'\n')
print('PASS 4 cone datasets and 182 animation frames')
