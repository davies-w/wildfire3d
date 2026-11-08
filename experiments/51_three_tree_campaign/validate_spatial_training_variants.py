import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r))
from spatial_training_variants import matrix,sha
checks=[]
for case in ['tree51_001323_baseline','tree51_001336_baseline']:
 base=np.load(r/'data/training-preview'/case/'training.npz');root=r/'data/spatial-training-variants'/case
 for kind,n in [('cone',11),('ellipsoid',15)]:
  p=root/kind;d=np.load(p/'training.npz');x=d['state'];t=d['time_s'];s=d['source_spatial_state'];st=d['source_time_s']
  assert x.shape==(91,n) and np.isfinite(x).all()
  assert np.array_equal(x[:,:4],base['state'][:,:4])
  assert d['observed'].sum()==6 and d['interpolated'].sum()==85
  assert t.min()>=st.min() and t.max()<=st.max()
  for j,tt in enumerate(st):assert np.array_equal(x[np.flatnonzero(t==tt)[0],4:],s[j])
  for row in x[:,4:]:
   if row[0]==0:assert (row==0).all()
   elif kind=='cone':assert abs(np.linalg.norm(row[1:4])-1)<1e-12 and (row[4:6]>=0).all()
   else:assert np.linalg.eigvalsh(matrix(row[4:10])).min()>0
  sample=json.loads((p/'first-transition.json').read_text());assert np.array_equal(sample['initial_state']['values'],x[0]);assert np.array_equal(sample['next_state']['values'],x[1])
  assert sample['no_hidden_history_window']
  checks.append({'case':case,'variant':kind,'rows':91,'states':n,'observed':6,'interpolated':85,'sha256':sha(p/'training.npz')})
 assert Image.open(root/'comparison-3d.gif').n_frames==91
(r/'data/spatial-training-variants/validation.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2)+'\n')
print('PASS four datasets, original four channels, exact observed endpoints, valid geometry, first-step examples, 182 animation frames')
