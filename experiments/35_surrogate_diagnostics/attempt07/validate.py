"""Synthetic CPU checks only; no optimization. CUDA replay mandatory on worker."""
from pathlib import Path
import json,torch,numpy as np
from model import HotUNet,metrics
R=Path(__file__).parent;torch.set_num_threads(4);p=json.loads((R/'coverage-plan.json').read_text());a=json.loads((R/'results/labels-audit.json').read_text());assert len(a['cases'])==400 and p['selected_frames']==list(range(0,91,10));assert p['architecture'].find('13inputs')>=0
m=HotUNet();x=torch.zeros(1,13,48,32,32);y=m(x);assert y.shape==(1,48,32,32) and torch.isfinite(y).all();y.mean().backward();assert all(z.grad is None or torch.isfinite(z.grad).all() for z in m.parameters())
assert metrics([1,0,0,1])['f1']==1 and metrics([0,0,1,1])['recall']==0 and metrics([0,0,0,2])['recall'] is None
train=[c for c in json.loads((R/'cases.json').read_text()) if c['split']=='train'];assert len(train)==360;z=np.load(R/'data/labels'/(train[0]['case']+'.npz'));assert np.unpackbits(z['packed'],axis=1,count=49152).sum()==z['positive'].sum()
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,parameters=sum(z.numel() for z in m.parameters()),scope='Synthetic CPU architecture forward/backward, metric edgecases, label bitpacking,split checks; no optimizer. Mandatory actualCUDA replay and gradients before paidtraining.'),indent=2))
