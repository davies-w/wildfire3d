from pathlib import Path
import torch,json,numpy as np,hashlib,ast,textwrap
from objective import interval_error,sequence_score
R=Path(__file__).resolve().parent;D=R/'data/training06'
x=torch.tensor([2.,-2.,0.,1.]);y=torch.tensor([2.,2.,0.,-3.]);assert torch.allclose(interval_error(x,y),torch.tensor([2.,1.,0.,1.25]))
p=torch.tensor([[[0.],[2.],[-2.]]],dtype=torch.float64,requires_grad=True);q=torch.zeros_like(p);t=torch.tensor([[0.,1.,3.]],dtype=torch.float64);rg=torch.tensor([[4.]],dtype=torch.float64)
assert torch.allclose(sequence_score(p,q,t,rg),torch.tensor([[.25]],dtype=torch.float64));sequence_score(p,q,t,rg).sum().backward();assert torch.isfinite(p.grad).all()
z=torch.zeros(3,requires_grad=True);interval_error(z,z).sum().backward();assert torch.isfinite(z.grad).all()
s=(D/'worker.py').read_text();compile(s,'worker','exec');frag=s[s.index('   left_error='):s.index("assert bool(torch.isfinite(loss)),f'Nonfinite")];compile(textwrap.dedent(frag),'loss','exec')
assert "range(0,91-h)" in s and "assert len(reports)==1" in s and s.index("save('selection-freeze.json'")<s.index('tests=[]')
meta=json.loads((D/'schema.json').read_text());rot=meta['rotations'][0]
for a,b in [('train','validation'),('train','test'),('validation','test')]:assert not set(rot[a])&set(rot[b])
assert len(rot['train'])==1664 and len(rot['validation'])==208 and len(rot['test'])==208
old=R/'data/training03'
for n in ['model.py','gated_model.py','plain_model.py','objective.py','data/sequences.npz']:assert (D/n).read_bytes()==(old/n).read_bytes()
full=json.loads((R.parent/'36_tree_density/data/model-training/schema.json').read_text());assert rot==full['rotations'][3]
a=np.load(D/'data/sequences.npz');cfg=a['configuration']
for x,y in [('train','validation'),('train','test'),('validation','test')]:assert not set(cfg[rot[x]])&set(cfg[rot[y]])
p=json.loads((D/'coverage-plan.json').read_text());prior=json.loads((old/'coverage-plan.json').read_text());assert p==json.loads(json.dumps(prior).replace('rotation0','rotation3').replace('57600','86400'))
assert s== (old/'worker.py').read_text().replace('unchanged rotation0 train8/val1/test1 split','frozen rotation3 train8/val1/test1 split')
for p in [*R.glob('*.py'),*D.glob('*.py')]:ast.parse(p.read_text())
proof=dict(passed=True,exact_integral_fixtures=True,zero_gradient_finite=True,split_and_model_unchanged=True,local_optimizer=False,cloud_timing_and_resume_required=True)
(R/'results06/offline-check.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

assert (D/'cloud_check.py').read_bytes()==(R/'cloud_check06.py').read_bytes()
import yaml
w=yaml.safe_load((D/'workflow.yaml').read_text());j=w['main']['steps'][0]['initialize']['assign'][0]['job'];assert j['allocationPolicy']['instances'][0]['policy']['accelerators']==[{'type':'nvidia-tesla-t4','count':1}]
assert j['taskGroups'][0]['taskSpec']['maxRunDuration']=='87300s'
assert 'queue_deadline' not in (D/'workflow.yaml').read_text()

assert j['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT'
assert j['allocationPolicy']['location']['allowedLocations']==['zones/us-west1-a','zones/us-west1-b']
