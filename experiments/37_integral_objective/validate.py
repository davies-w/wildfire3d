from pathlib import Path
import torch,json,numpy as np,hashlib,ast,textwrap
from objective import interval_error,sequence_score
R=Path(__file__).resolve().parent;D=R/'data/training01'
x=torch.tensor([2.,-2.,0.,1.]);y=torch.tensor([2.,2.,0.,-3.]);assert torch.allclose(interval_error(x,y),torch.tensor([2.,1.,0.,1.25]))
p=torch.tensor([[[0.],[2.],[-2.]]],dtype=torch.float64,requires_grad=True);q=torch.zeros_like(p);t=torch.tensor([[0.,1.,3.]],dtype=torch.float64);rg=torch.tensor([[4.]],dtype=torch.float64)
assert torch.allclose(sequence_score(p,q,t,rg),torch.tensor([[.25]],dtype=torch.float64));sequence_score(p,q,t,rg).sum().backward();assert torch.isfinite(p.grad).all()
z=torch.zeros(3,requires_grad=True);interval_error(z,z).sum().backward();assert torch.isfinite(z.grad).all()
s=(D/'worker.py').read_text();compile(s,'worker','exec');frag=s[s.index('   left_error='):s.index("assert bool(torch.isfinite(loss)),f'Nonfinite")];compile(textwrap.dedent(frag),'loss','exec')
assert "range(0,91-h)" in s and "assert len(reports)==1" in s and s.index("save('selection-freeze.json'")<s.index('tests=[]')
meta=json.loads((D/'schema.json').read_text());rot=meta['rotations'][0]
for a,b in [('train','validation'),('train','test'),('validation','test')]:assert not set(rot[a])&set(rot[b])
assert len(rot['train'])==1662 and len(rot['validation'])==210 and len(rot['test'])==208
old=R.parent/'36_tree_density/data/pair-sequence/rotation0'
for n in ['gated_model.py','schema.json','data/sequences.npz']:assert (D/n).read_bytes()==(old/n).read_bytes()
for p in [*R.glob('*.py'),*D.glob('*.py')]:ast.parse(p.read_text())
proof=dict(passed=True,exact_integral_fixtures=True,zero_gradient_finite=True,split_and_model_unchanged=True,local_optimizer=False,cloud_timing_and_resume_required=True)
(R/'results/offline-check.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
