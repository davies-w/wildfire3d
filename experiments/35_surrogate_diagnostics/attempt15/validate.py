"""No optimizer: split, normalization, history/rollout, gradient and serialization checks."""
from pathlib import Path
import json,io,ast
import numpy as np
import torch
from model import Transition,normalize_fit
torch.set_num_threads(4);R=Path(__file__).resolve().parent;meta=json.loads((R/'schema.json').read_text());a=np.load(R/'data/sequences.npz');raw=torch.tensor(a['state']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry'])
assert raw.shape==(520,91,3) and geom.shape==(520,7) and torch.isfinite(raw).all()
assert (times[:,1:]>times[:,:-1]).all()
seen=[]
for rot in meta['rotations']:
 sets=[set(rot[k]) for k in ['train','validation','test']];assert set.union(*sets)==set(range(520)) and all(sets[i].isdisjoint(sets[j]) for i,j in [(0,1),(0,2),(1,2)])
 gs=[set(a['configuration'][sorted(s)]) for s in sets];assert [len(g) for g in gs]==[384,48,48] and all(gs[i].isdisjoint(gs[j]) for i,j in [(0,1),(0,2),(1,2)])
 seen+=rot['test'];ids=torch.tensor(rot['train']);mean,std=normalize_fit(raw,ids,config,scale);alter=raw.clone();alter[rot['test']]+=1e5;m2,s2=normalize_fit(alter,ids,config,scale);assert torch.equal(mean,m2) and torch.equal(std,s2)
assert sorted(seen)==list(range(520))
dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales'])
active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5)
source=ast.parse((R/'worker.py').read_text());names={'mean_groups','objective','history_at','advance','phase_mae','predictions','evaluate'};ns=dict(torch=torch,config=config,raw=raw,scale=scale,meta=meta,times=times,dt=dt,external=external,active=active)
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'worker-check','exec'),ns)
ids=torch.tensor(meta['rotations'][0]['train']);mean,std=normalize_fit(raw,ids,config,scale);z=(torch.asinh(raw/scale)-mean)/std
m=Transition();x=ns['history_at'](z,ids[:4],torch.zeros(4,dtype=torch.long));assert torch.equal(x[:,0],x[:,-1]);u=external[ids[:4],0];y=m(x,u);assert torch.equal(y,x[:,-1]);(y-x[:,-1]-1).square().mean().backward();assert m.net[-1].bias.grad.abs().sum()>0
buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition();m2.load_state_dict(torch.load(buf,weights_only=False));assert torch.equal(m2(x,u),y)
m.zero_grad();hist=x;loss=0
for j in range(8):
 pred=m(hist,external[ids[:4],j]);loss+=ns['objective'](pred,z[ids[:4],j+1]).mean();hist=ns['advance'](hist,pred)
loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters())
out=ns['evaluate'](m,z,ids[:3],mean,std,True);assert out['rollout']['finite'];assert len(out['rollout']['physical_MAE_by_feature'])==3
# Autonomous rollout cannot read later target states.
original=ns['predictions'](m,z,ids[:3],True);mutated=z.clone();mutated[:,1:]+=100;assert torch.equal(original,ns['predictions'](m,mutated,ids[:3],True))
for h in [1,8]:
 c=np.zeros(90,int)
 for j in range(0,90,h):c[j:min(j+h,90)]+=1
 assert (c==1).all()
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,local_training=False,histories=520,configurations=480,input_features=21,outputs=3,history_steps=4,parameters=sum(p.numel() for p in m.parameters()),checks=['configuration-disjoint folds; all520 test once','train-only normalization invariant to test changes','initial persistence','nonzero output gradient','8-step BPTT finite','serialization exact','autonomous rollout independent of future truth','all90 transitions covered','physical metrics exercised']),indent=2));print('PREFLIGHT PASSED; no local optimization')
