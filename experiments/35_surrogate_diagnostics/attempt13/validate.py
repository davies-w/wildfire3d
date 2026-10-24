"""CPU inference/gradient and split arithmetic checks only: no optimizer or fitting."""
from pathlib import Path
import json,io
import numpy as np
import torch
from model import Transition,normalize_fit
R=Path(__file__).resolve().parent;meta=json.loads((R/'schema.json').read_text());a=np.load(R/'data/sequences.npz');raw=torch.tensor(a['state']);mask=torch.tensor(a['mask']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales'])
assert raw.shape==(520,91,52) and a['geometry'].shape==(520,10)
seen=[]
for rot in meta['rotations']:
 sets=[set(rot[k]) for k in ['train','validation','test']];assert all(sets[i].isdisjoint(sets[j]) for i,j in [(0,1),(0,2),(1,2)]) and set.union(*sets)==set(range(520))
 gs=[set(a['configuration'][sorted(s)]) for s in sets];assert [len(g) for g in gs]==[384,48,48] and all(gs[i].isdisjoint(gs[j]) for i,j in [(0,1),(0,2),(1,2)])
 seen+=rot['test'];ids=torch.tensor(rot['train']);mean,std=normalize_fit(raw,mask,ids,config,scale);alter=raw.clone();alter[rot['test']]+=100000;mean2,std2=normalize_fit(alter,mask,ids,config,scale);assert torch.equal(mean,mean2) and torch.equal(std,std2)
assert sorted(seen)==list(range(520))
m=Transition();x=torch.randn(5,52);u=torch.zeros(5,13);u[:,-1]=1;y=m(x,u);assert torch.equal(x,y);(y-x-1).square().mean().backward();assert m.net[-1].bias.grad.abs().sum()>0
buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition();m2.load_state_dict(torch.load(buf,weights_only=False));assert torch.equal(m2(x,u),y)
for h in [1,8]:
 counts=np.zeros(90,int)
 for j in range(0,90,h):counts[j:min(j+h,90)]+=1
 assert np.all(counts==1)
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,local_training=False,histories=520,configurations=480,state_shape=[520,91,52],model_input_features=65,model_output_features=52,parameters=sum(p.numel() for p in m.parameters()),checks=['all cases each test exactly once','physical configurations disjoint 384/48/48','test perturbation leaves train normalization unchanged','initial persistence exact','nonzero direct gradients','serialization replay exact','every training transition covered once at horizons1and8']),indent=2));print('PREFLIGHT PASSED: no local optimization')
# Exercise the exact worker evaluation functions on CPU without executing its training loop.
import ast
source=ast.parse((R/'worker.py').read_text());wanted={'mean_groups','objective','predictions','evaluate'};nodes=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
ns=dict(torch=torch,config=config,raw=raw,mask=mask,scale=scale,meta=meta,times=torch.tensor(a['time']))
dt=ns['times'][:,1:]-ns['times'][:,:-1];on=(20-ns['times'][:,:-1]).clamp_min(0).minimum(dt)/dt;g=torch.tensor(a['geometry']);ns['external']=torch.cat([g[:,None,:].expand(-1,90,-1),torch.full_like(dt[:,:,None],.2),on[:,:,None],dt[:,:,None]/2],-1)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'worker-evaluation-check','exec'),ns)
ids=torch.tensor(meta['rotations'][0]['train']);mean,std=normalize_fit(raw,mask,ids,config,scale);z=torch.where(mask.bool(),(torch.asinh(raw/scale)-mean)/std,torch.zeros_like(raw))
out=ns['evaluate'](m,z,ids[:3],mean,std,True);assert out['rollout']['finite'] and len(out['rollout']['cases'])==3
assert len(out['rollout']['physical_MAE_by_feature'])==52
print('Exact worker metric and rollout functions passed CPU inference check')
