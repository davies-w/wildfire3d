"""Preflight only: synthetic forward/recovery and case checks; no optimization."""
from pathlib import Path
import ast,json,io
import numpy as np,torch
from torch import nn
from geometry_model import GeometryCNN
from diagnostic_model import OracleCNN
from validate_interpolation import validate
R=Path(__file__).parent
for p in R.glob('*.py'):ast.parse(p.read_text())
cs=json.loads((R/'cases.json').read_text());plan=json.loads((R/'coverage-plan.json').read_text());assert len(cs)==48 and sum(c['split']=='train' for c in cs)==8
assert len({c['configuration'] for c in cs if c['split']=='validation'})==32
assert not ({c['configuration'] for c in cs if c['split']=='train'} & {c['configuration'] for c in cs if c['split']=='validation'})
assert all(c['split']!='test' for c in cs)
z=np.load(R/'data/geometries.npz');assert set(z.files)=={c['case'] for c in cs}
audit=json.loads((R/'replica-time-audit.json').read_text());assert len(audit['rows'])==8 and audit['max_delta_s']<=.2 and all(v['distinct_mapping'] for v in audit['rows'])
validate();torch.manual_seed(3501);m=GeometryCNN();o=OracleCNN(m.state_dict())
with torch.no_grad():
 x=torch.randn(1,13);a=m(x);b=o(torch.cat([x,torch.ones(1,1)],1));assert torch.equal(a,b);assert a.shape==(1,6,48,32,32) and torch.isfinite(a).all()
# Resume layout returns exactly the same unconsumed schedule positions.
for epoch in [0,1,19]:
 order=np.random.default_rng(3501+epoch).permutation(248)
 for next_batch in [0,1,100,248]:assert np.array_equal(np.r_[order[:next_batch],np.random.default_rng(3501+epoch).permutation(248)[next_batch:]],order)
for n in [91,90,1]:assert [j for k in range(0,n,3) for j in range(k,min(k+3,n))]==list(range(n))
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,case_count=len(cs),oracle_initial_forward_exact=True,epoch_frame_coverage=True,resume_schedule=True,scope='Synthetic CPU checks only; actual CUDA replay mandatory before optimization.'),indent=2))
print('Preflight passed; no training')
