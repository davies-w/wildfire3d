"""No optimizer: split, normalization, history/rollout, gradient and serialization checks."""
from pathlib import Path
import json,io,ast
import numpy as np
import torch
from model import Transition,normalize_fit
torch.set_num_threads(4);R=Path(__file__).resolve().parent;meta=json.loads((R/'schema.json').read_text());a=np.load(R/'data/sequences.npz');raw=torch.tensor(a['state']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry'])
assert raw.shape==(520,91,7) and geom.shape==(520,7) and torch.isfinite(raw).all()
assert (times[:,1:]>times[:,:-1]).all()
seen=[]
for rot in meta['rotations']:
 sets=[set(rot[k]) for k in ['train','validation','test']];assert set.union(*sets)==set(range(520)) and all(sets[i].isdisjoint(sets[j]) for i,j in [(0,1),(0,2),(1,2)])
 gs=[set(a['configuration'][sorted(s)]) for s in sets];assert [len(g) for g in gs]==[384,48,48] and all(gs[i].isdisjoint(gs[j]) for i,j in [(0,1),(0,2),(1,2)])
 seen+=rot['test'];ids=torch.tensor(rot['train']);mean,std=normalize_fit(raw,ids,config,scale);alter=raw.clone();alter[rot['test']]+=1e5;m2,s2=normalize_fit(alter,ids,config,scale);assert torch.equal(mean,m2) and torch.equal(std,s2)
assert sorted(seen)==list(range(520))
dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales'])
active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5)
source=ast.parse((R/'worker.py').read_text());names={'mean_groups','objective','training_objective','history_at','advance','phase_mae','prefix_memory','predictions','evaluate','horizon_metrics'};ns=dict(torch=torch,config=config,raw=raw,scale=scale,meta=meta,times=times,dt=dt,external=external,active=active,device="cpu",P={"evaluation_horizons":[1,4]})
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'worker-check','exec'),ns)
ids=torch.tensor(meta['rotations'][0]['train']);mean,std=normalize_fit(raw,ids,config,scale);z=(torch.asinh(raw/scale)-mean)/std
checks=[]
torch.manual_seed(3516);ma=Transition('scalar');torch.manual_seed(3516);mb=Transition('spatial');assert all(torch.equal(x,y) for x,y in zip(ma.state_dict().values(),mb.state_dict().values()))
for kind in ['scalar','spatial']:
 if kind=='scalar':
  armraw=raw.clone();armraw[:,:,4:]=0
 else:armraw=raw.clone()
 mean,std=normalize_fit(armraw,ids,config,scale);z=(torch.asinh(armraw/scale)-mean)/std;ns['raw']=armraw
 m=Transition(kind);x=ns['history_at'](z,ids[:4],torch.zeros(4,dtype=torch.long));u=external[ids[:4],0];y,mem=m.step(x,u);assert torch.equal(y,x[:,-1])
 # Nonzero readout exercises recurrent dependence, without any optimizer.
 with torch.no_grad():
  head=m.head;head.weight.fill_(.001)
 y,mem=m.step(x,u);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition(kind);m2.load_state_dict(torch.load(buf,weights_only=False));assert torch.equal(m2(x,u),y)
 hist=x;memory=None;loss=0
 for j in range(32):
  pred,memory=m.step(hist,external[ids[:4],j],memory);loss+=ns['objective'](pred,z[ids[:4],j+1]).mean();hist=ns['advance'](hist,pred)
 loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
 if kind in ['scalar','spatial']:assert m.cell.weight_hh_l0.grad.abs().sum()>0
 original=ns['predictions'](m,z,ids[:3],True);mutated=z.clone();mutated[:,1:]+=100;assert torch.equal(original,ns['predictions'](m,mutated,ids[:3],True))
 # Teacher-forced prefix memory must be independent of states beyond origin.
 js=torch.tensor([4,8,12]);ii=ids[:3];first=ns['prefix_memory'](m,z,ii,js);alt=z.clone()
 for n,j in zip(ii.tolist(),js.tolist()):alt[n,j+1:]+=100
 second=ns['prefix_memory'](m,alt,ii,js)
 if kind in ['scalar','spatial']:assert torch.equal(first,second)
 out=ns['evaluate'](m,z,ii,mean,std,True);assert out['rollout']['finite']
 # At horizon one, cached GRU teacher-memory equals direct sequential evaluation.
 one=ns['predictions'](m,z,ii,False)
 for j in [0,4,30,89]:
  jj=torch.full_like(ii,j);h0=ns['history_at'](z,ii,jj);hmem=ns['prefix_memory'](m,z,ii,jj);direct,_=m.step(h0,external[ii,j],hmem);assert torch.allclose(direct,one[:,j],atol=1e-6,rtol=1e-6)
 hm=ns['horizon_metrics'](m,z,ii,mean,std);assert all(v['finite'] for v in hm.values())
 checks.append(dict(kind=kind,parameters=sum(p.numel() for p in m.parameters()),checks=['initial persistence','32step backward all parameters finite','serialization exact','no future truth in autonomous or prefix','one-step cached memory equivalence']))
for h in [1,8,16,32]:
 count=np.zeros(90,int)
 for j in range(0,90,h):count[j:min(j+h,90)]+=1
 assert (count==1).all()
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,local_training=False,histories=520,configurations=480,checks=checks,matched_shuffle='same rotation/epoch seed for both arms',split_normalization_tests=True),indent=2));print('PREFLIGHT PASSED',checks)
