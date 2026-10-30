"""Offline architecture/data checks; no optimizer or model fitting."""
from pathlib import Path
import sys,json,ast,io,hashlib
import numpy as np
import torch,yaml
R=Path(__file__).resolve().parent;D=R/'data/training03';sys.path.insert(0,str(D))
from model import Transition,normalize_fit
from objective import interval_error,sequence_score
torch.set_num_threads(4);torch.manual_seed(3516)
m=Transition('gated');assert sum(p.numel() for p in m.parameters())==25159
assert m.cell.input_size==41 and m.cell.hidden_size==64 and m.cell.num_layers==1
assert isinstance(m.shared[1],torch.nn.SiLU) and m.head.out_features==4 and m.gate_head.out_features==3
src=(D/'worker.py').read_text();tree=ast.parse(src);names=['history_at','advance','prefix_memory','predictions'];ns={'torch':torch}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'worker-functions','exec'),ns)
z=torch.randn(3,91,4);ext=torch.randn(3,90,9)*.05;ext[:,:,-1]=1;ns['external']=ext
ids=torch.arange(3);js=torch.tensor([0,4,20]);hist=ns['history_at'](z,ids,js);assert hist.shape==(3,8,4)
assert torch.equal(hist[0],z[0,:1].expand(8,-1));assert torch.equal(hist[2],z[2,13:21])
with torch.no_grad():
 m.head.weight.normal_(0,.002);m.gate_head.weight.normal_(0,.002)
 memory=ns['prefix_memory'](m,z,ids,js)
 for i,j in enumerate(js):
  mm=None
  for t in range(int(j)):
   _,mm=m.step(ns['history_at'](z,ids[i:i+1],torch.tensor([t])),ext[i:i+1,t],mm)
  if mm is not None:assert torch.allclose(memory[i],mm[0],atol=2e-6,rtol=2e-5)
  else:assert torch.equal(memory[i],torch.zeros(64))
 first=ns['predictions'](m,z,ids,True);changed=z.clone();changed[:,1:]+=100
 assert torch.equal(first,ns['predictions'](m,changed,ids,True)), 'Autonomous rollout read future truth'
 q=m(hist,ext[:,0]);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition('gated');m2.load_state_dict(torch.load(buf,weights_only=False));assert torch.equal(q,m2(hist,ext[:,0]))
# Both heads propagate gradients through the shared layer; 32-step gradients finite.
m.zero_grad();hist=ns['history_at'](z,ids,torch.zeros(3,dtype=torch.long));mem=None;loss=0
for j in range(32):
 state,mem=m.step(hist,ext[:,j],mem);loss=loss+state.square().mean()+m.last_gate_logits.square().mean();hist=ns['advance'](hist,state)
loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters());assert m.shared[0].weight.grad.abs().sum()>0
meta=json.loads((D/'schema.json').read_text());prior=json.loads((R.parent/'37_integral_objective/data/training03/schema.json').read_text());assert meta['rotations']==prior['rotations'];rot=meta['rotations'][0]
a=np.load(D/'data/sequences.npz');cfg=a['configuration'];assert [len(rot[k]) for k in ['train','validation','test']]==[1662,210,208]
for x,y in [('train','validation'),('train','test'),('validation','test')]:assert not set(cfg[rot[x]])&set(cfg[rot[y]])
raw=torch.tensor(a['state']);scale=torch.tensor(meta['physical_encoding_scales']);tr=torch.tensor(rot['train']);config=torch.tensor(cfg)
mean,std=normalize_fit(raw,tr,config,scale);raw[rot['validation']+rot['test']]+=10000;other=normalize_fit(raw,tr,config,scale);assert torch.equal(mean,other[0]) and torch.equal(std,other[1])
assert (D/'objective.py').read_bytes()==(R.parent/'37_integral_objective/data/training03/objective.py').read_bytes()
assert (D/'data/sequences.npz').read_bytes()==(R.parent/'37_integral_objective/data/training03/data/sequences.npz').read_bytes()
p=json.loads((D/'coverage-plan.json').read_text());old=json.loads((R.parent/'37_integral_objective/data/training06/coverage-plan.json').read_text())
for k in old:
 if k not in ['experiment','history_steps','input_features','history','architecture','test','budget']:assert p[k]==old[k],k
assert p['history_steps']==8 and p['input_features']==41
assert "range(0,91-h)" in src and src.index("save('selection-freeze.json'")<src.index('tests=[]')
w=yaml.safe_load((D/'workflow.yaml').read_text());j=w['main']['steps'][0]['initialize']['assign'][0]['job'];policy=j['allocationPolicy']['instances'][0]['policy']
assert policy['provisioningModel']=='SPOT' and policy['accelerators']==[{'type':'nvidia-tesla-t4','count':1}]
assert j['allocationPolicy']['location']['allowedLocations']==['zones/us-west1-a']
assert 'queue_deadline' not in (D/'workflow.yaml').read_text()
proof=dict(passed=True,parameters=25159,history_steps=8,hidden_units=64,shared_units=64,activation='SiLU',three_gates_retained=True,split_rotation=0,configuration_disjoint=True,normalization_train_only=True,prefix_equivalence=True,no_future_truth=True,serialization=True,backward32=True,recipe_preserved=True,local_optimizer=False,cloud_timing_and_resume_required=True)
(R/'results03/offline-check.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
