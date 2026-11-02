"""CPU forward-only validation of the actual ten-value history and rollout paths."""
from pathlib import Path
import sys,json,io,hashlib,ast
sys.dont_write_bytecode=True
import numpy as np,torch
R=Path(__file__).resolve().parent;D=R/'data/training';sys.path.insert(0,str(D));torch.set_num_threads(4)
from model import Transition
schema=json.loads((D/'schema.json').read_text());rot=schema['rotations'][0];a=np.load(D/'data/sequences.npz');c=np.load(D/'data/cones.npz')
assert c['parameters'].shape==(2080,91,5) and c['active'].shape==(2080,91) and np.array_equal(a['time'],c['time']);assert np.isfinite(c['parameters']).all()
sets={s:{tuple(schema['cases'][i]['physical_key']) for i in rot[s]} for s in ['train','validation','test']}
assert all(not sets[x]&sets[y] for x,y in [('train','validation'),('train','test'),('validation','test')]);assert [len(rot[s]) for s in sets]==[1662,210,208]
torch.manual_seed(3516);m=Transition('gated');assert sum(p.numel() for p in m.parameters())==34765;assert m.cell.input_size==89 and m.cell.num_layers==1;assert not any(isinstance(v,torch.nn.Dropout) for v in m.modules())
# Execute the exact worker definition section, replacing only cloud I/O and device.
src=(D/'worker.py').read_text().split('checks=[]')[0].replace('from runtime import upload','def upload(*args): raise AssertionError("No local cloud write")').replace("assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'",'').replace("device='cuda'","device='cpu'")
ns={'__file__':str(D/'worker.py')};exec(compile(src,'<worker-forward-definitions>','exec'),ns)
with torch.no_grad():
 mean,std=ns['normalize_fit'](ns['raw'],torch.tensor(rot['train']),ns['config'],ns['scale']);z=ns['recurrent_states']((torch.asinh(ns['raw']/ns['scale'])-mean)/std);assert z.shape==(2080,91,10)
 m.set_normalization(mean,std);ids=torch.tensor(rot['train'][:4]);js=torch.tensor([0,1,5,12]);h=ns['history_at'](z,ids,js);u=ns['external'][ids,js];assert h.shape==(4,8,10)
 assert torch.equal(h[...,4],c_tensor:=torch.tensor(c['active'])[ids[:,None],(js[:,None]+torch.arange(-7,1)).clamp_min(0)].float())
 m.eval();q,mem=m.step(h,u);assert q.shape==(4,10);assert torch.equal(q[:,4],torch.sigmoid(m.last_cone_logit));assert torch.equal(q[:,5:],m.last_cone/m.cone_scales)
 f=io.BytesIO();torch.save(m.state_dict(),f);f.seek(0);n=Transition('gated');n.load_state_dict(torch.load(f,weights_only=False));assert torch.equal(q,n(h,u))
 # Every added field at every history position is an actual GRU input.
 for j in range(8):
  for k in range(4,10):
   changed=h.clone();changed[:,j,k]+=.2;_,other=m.step(changed,u);assert not torch.equal(mem,other),(j,k)
 # Prefix uses only truth through the origin; future truth changes cannot affect it.
 before=ns['prefix_memory'](m,z,ids,js);future=z.clone()
 for i,j in zip(ids,js):future[i,int(j)+1:]+=9
 assert torch.equal(before,ns['prefix_memory'](m,future,ids,js))
 for row,(i,j) in enumerate(zip(ids,js)):
  mm=None
  for t in range(int(j)):
   hh=ns['history_at'](z,i[None],torch.tensor([t]));_,mm=m.step(hh,ns['external'][i[None],t],mm)
  assert torch.allclose(before[row],torch.zeros(64) if mm is None else mm[0],atol=2e-6,rtol=2e-5)
 # Actual predictions() must consume all ten outputs at the following step.
 seen=[];outputs=[];original=m.step
 def recording(history,external,memory=None):
  seen.append(history.clone());out=original(history,external,memory);outputs.append(out[0].clone());return out
 m.step=recording;ns['predictions'](m,z,ids,True);m.step=original
 assert len(seen)==90 and all(torch.equal(seen[j][:,-1],outputs[j-1]) for j in range(1,90))
 # Current loss forward executes at all horizons, including no-future teacher prefix.
 fragment=(D/'worker.py').read_text();fragment=fragment[fragment.index('   cone_predictions=[]'):fragment.index("assert bool(torch.isfinite(loss)),f'Nonfinite")]
 import textwrap
 weights=torch.ones(2080)
 for horizon in [1,8,16,32,64,90]:
  origins=js.clamp_max(90-horizon);hist=ns['history_at'](z,ids,origins);context=dict(ns,model=m,z=z,mean=mean,std=std,ids=ids,js=origins,h=horizon,hist=hist,memory=ns['prefix_memory'](m,z,ids,origins),replica_weights=weights)
  exec(compile(textwrap.dedent(fragment),'<actual-loss-forward>','exec'),context);assert torch.isfinite(context['loss']);assert context['hist'].shape==(4,8,10)
assert not (D/'data/resume').exists()
proof=dict(passed=True,scope='CPU forward-only; no optimizer or backward. Cloud optimizer/backward checks remain required.',parameters=34765,history_steps=8,state_values=10,external_values=9,gru_inputs=89,cone_inputs=True,all_48_cone_history_fields_affect_memory=True,all_ten_predictions_fed_back=True,no_future_truth_prefix=True,all_six_actual_loss_forward=True,serialization_bitwise=True,split_histories=[1662,210,208],dropout=False,fresh_seed=3516)
(R/'validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
