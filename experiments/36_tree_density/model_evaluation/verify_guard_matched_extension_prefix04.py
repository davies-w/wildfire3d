"""After terminal collection, check that longer fitting reproduces the old300epoch state."""
from pathlib import Path
import json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1]
assert json.loads((R/'results/guard-matched-pilot04-collected.json').read_text())['experiment_complete']
assert json.loads((R/'results/guard-matched-pilot04-collected.json').read_text())['cleanup_verified']
def equal(a,b):
 if torch.is_tensor(a):return torch.is_tensor(b) and a.dtype==b.dtype and a.shape==b.shape and torch.equal(a,b)
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,(tuple,list)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b
rows=[]
for arm in ['aggregate_control','balanced_tail']:
 old=torch.load(R/f'data/guard-matched-pilot01-results/{arm}-epoch300.pt',map_location='cpu',weights_only=False)
 new=torch.load(R/f'data/guard-matched-pilot04-results/{arm}-epoch300.pt',map_location='cpu',weights_only=False)
 checks={k:equal(old[k],new[k]) for k in ['model','optimizer','rng','epoch','batch_cursor','case_permutation','origin_choices']}
 rows.append(dict(arm=arm,checks=checks));assert all(checks.values()),rows[-1]
out=dict(passed=True,arms=rows,optimizer_updates=0,scope='Exact300epoch endpoint model, optimizer, RNG and data cursor equality with the previous run. Combined with identical source/initialization/draw rule, checks preservation of the original fitting prefix. Does not prove accuracy or generalization; no checkpoint choice is changed.')
(R/'results/guard-matched-pilot04-prefix-replay.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
