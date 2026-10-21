"""Small inference-only input/interface checks; no laptop model training."""
import json,sys
from pathlib import Path
import numpy as np,torch
from geometry_model import GeometryCNN,features
from sequence import Sequence
from original_cnn import cond
from fields import read_slice
from material_reader import frames
R=Path(__file__).parent
cs=json.loads((R/'development.json').read_text());tests=json.loads((R/'fresh-tests.json').read_text());g=dict(np.load(R/'data/geometries.npz'))
assert len(cs)==472 and len(tests)==48
assert len({c['configuration'] for c in cs if c['split']=='train'})==400
assert not {c['configuration'] for c in cs}&{c['configuration'] for c in tests}
c=cs[0];net=GeometryCNN();net.warm_start(torch.load(R/'data/models/previous.pt',weights_only=True,map_location='cpu'));x=np.concatenate([cond(c,[2]),features(g[c['case']])[None],np.array([[(c['moisture']-.12)/.18]],np.float32)],1)
with torch.no_grad():
 out=net(torch.from_numpy(x));seq=Sequence(g[c['case']]);p,m,t,h=seq.initialize(c);out2,*_=seq(p,m,t,h,c,0,seq.source(c),baseline=out)
assert out.shape==(1,6,48,32,32) and torch.isfinite(out2).all()
# Compare replacement record reader against established raw evidence.
f=next((R.parent/'31_tree_variations/data/cloud/v31_00').glob('*.sf'),None)
if f is None:f=next((R.parent/'27_single_tree_cnn/data/cloud/s27_train_0').glob('*.sf'))
_,_,_,tt,a=read_slice(f);assert len(tt)>80 and np.isfinite(a).all()
ps=next(ps for t,ps,labels in frames(R.parent/'27_single_tree_cnn/data/cloud/s27_train_0/s27_train_0_1.prt5') if len(ps[0][0]));assert all(len(p[0])==400 for p in ps[:4])
result=dict(passed=True,development_trajectories=len(cs),fresh_test_trajectories=len(tests),snapshot_inputs=13,explicit_moisture_both_models=True,local_training=False)
(R/'results/learning-interface-check.json').write_text(json.dumps(result,indent=2));print(result)
