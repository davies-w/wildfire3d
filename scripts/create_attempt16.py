"""Create the explicitly authorized MLP/GRU longer-horizon comparison; no launch."""
from pathlib import Path
import json,shutil
repo=Path(__file__).resolve().parents[1];old=repo/'experiments/35_surrogate_diagnostics/attempt15';r=old.parent/'attempt16';r.mkdir(exist_ok=False);(r/'data').mkdir();(r/'results').mkdir()
for name in ['cloud.py','runtime.py','launch.py','collect.py','prepare_pilot.py','finish_run.py','finalize_archive.py']:
 s=(old/name).read_text().replace('attempt15','attempt16').replace('min35-15','memory35-16').replace('gpu35-min15','gpu35-memory16').replace('exp35-min15','exp35-memory16')
 if name=='launch.py':
  s=s.replace("+3<=", "+6<=").replace("+3,2)","+6,2)").replace('allowance_usd=3','allowance_usd=6').replace('compute_allowance_usd=2.2','compute_allowance_usd=4.4').replace('ancillary_cleanup_allowance_usd=.8','ancillary_cleanup_allowance_usd=1.6').replace('expected_usd=[.5,1.2]','expected_usd=[2,4.5]')
 if name=='prepare_pilot.py':
  s=s.replace("'+ 12600'","'+ 23400'").replace("'+ 11100'","'+ 21900'").replace("'10800s'","'21600s'").replace('proposed_new_cap_usd=3','proposed_new_cap_usd=6').replace('estimated_usd=[0.5,1.2]','estimated_usd=[2,4.5]').replace('task_deadline_s=10800','task_deadline_s=21600').replace('vm_age_limit_s=11100','vm_age_limit_s=21900').replace('absolute_deadline_s=12600','absolute_deadline_s=23400')
 if name=='finalize_archive.py':s=s.replace('==10','==20').replace('minimal-material learning results','MLP and GRU longer-horizon comparison')
 (r/name).write_text(s)
p=json.loads((old/'coverage-plan.json').read_text());p.update(experiment='Matched MLP versus GRU sequence-memory comparison',seed=3516,arms=['mlp','gru'],horizon_curriculum=[{'first_epoch':1,'steps':1},{'first_epoch':21,'steps':8},{'first_epoch':41,'steps':16},{'first_epoch':61,'steps':32}],minimum_epochs=100,sequence_horizon_steps=32,selection='Minimum full autonomous validation objective across all trained epochs; patience resets at21/41/61; no stopping before100',architecture='MLP21->64->64->3 versus GRUCell21->32 plus32->3 readout; three states, four explicit history frames, GRU32 internal latent values',test='All20 selections frozen before either architecture tests; same ten grouped rotations; test not historically pristine',evaluation_horizons=[1,4,8,16,45],burn_in='GRU memory initialized zero; teacher-forced prefix up to each training window recomputed with current parameters under no_grad; gradients within window only. Full autonomous evaluation uses predicted states from initial time, never true future states.')
p['budget']=dict(expected_usd=[2,4.5],maximum_allowance_usd=6,task_seconds=21600,vm_seconds=21900,absolute_seconds=23400,soft_seconds=20400,queue_seconds=1200)
(r/'coverage-plan.json').write_text(json.dumps(p,indent=2))
(r/'prepare.py').write_text('''from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;(R/'data').mkdir(exist_ok=True);(R/'results').mkdir(exist_ok=True)
shutil.copyfile(R.parent/'attempt15/data/sequences.npz',R/'data/sequences.npz')
s=json.loads((R.parent/'attempt15/schema.json').read_text());s['comparison']='Same three physical states/splits; GRU adds32 internal latent values, no additional measured states'
(R/'schema.json').write_text(json.dumps(s,indent=2))
''')
# Keep normalization implementation byte-identical to the previous experiment.
model='''"""Matched finite-history and gated-memory transitions; no output clipping."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,kind='mlp'):
  super().__init__();self.kind=kind
  if kind=='mlp':
   self.net=nn.Sequential(nn.Linear(21,64),nn.SiLU(),nn.Linear(64,64),nn.SiLU(),nn.Linear(64,3));head=self.net[-1]
  else:
   assert kind=='gru';self.cell=nn.GRUCell(21,32);self.head=nn.Linear(32,3);head=self.head
  nn.init.zeros_(head.weight);nn.init.zeros_(head.bias)
 def step(self,history,external,memory=None):
  x=torch.cat([history.flatten(1),external],-1)
  if self.kind=='gru':memory=self.cell(x,memory);delta=self.head(memory)
  else:delta=self.net(x)
  return history[:,-1]+delta*external[:,-1:],memory
 def forward(self,history,external):return self.step(history,external)[0]
'''
(r/'model.py').write_text(model+'\ndef normalize_fit'+(old/'model.py').read_text().split('def normalize_fit',1)[1])
# Adapt the proven collector-compatible worker. Job indexes0..19 map to fold/index arm.
s=(old/'worker.py').read_text().replace('3515','3516')
start=s.index('@torch.no_grad()\ndef predictions');end=s.index('@torch.no_grad()\ndef evaluate',start)
s=s[:start]+'''@torch.no_grad()
def prefix_memory(model,z,ids,js):
 if model.kind=='mlp':return None
 memory=torch.zeros(len(ids),32,device=z.device)
 for j in range(int(js.max())):
  hist=history_at(z,ids,torch.full_like(ids,j));_,candidate=model.step(hist,external[ids,j],memory)
  memory=torch.where((js>j)[:,None],candidate,memory)
 return memory
@torch.no_grad()
def predictions(model,z,ids,rollout):
 if not rollout and model.kind=='mlp':
  ii=ids[:,None].expand(-1,90).flatten();jj=torch.arange(90,device=z.device).expand(len(ids),-1).flatten()
  return model(history_at(z,ii,jj),external[ii,jj]).reshape(len(ids),90,3)
 history=history_at(z,ids,torch.zeros_like(ids));out=[];memory=None
 for j in range(90):
  if not rollout:history=history_at(z,ids,torch.full_like(ids,j))
  state,memory=model.step(history,external[ids,j],memory);out.append(state);history=advance(history,state)
 return torch.stack(out,1)
'''+s[end:]
start=s.index('m=Transition().to(device);');end=s.index('reports=[]',start)
s=s[:start]+'''checks=[]
for kind in P['arms']:
 m=Transition(kind).to(device);b=torch.zeros(4,4,3,device=device);u=external[:4,0];q=m(b,u);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition(kind).to(device);m2.load_state_dict(torch.load(buf,weights_only=False,map_location=device));assert torch.equal(q,m2(b,u));q.sum().backward();g=[p.grad.clone() for p in m.parameters()];m.zero_grad();m(b,u).sum().backward();assert all(torch.equal(v,p.grad) for v,p in zip(g,m.parameters()))
 m.zero_grad();history=b;memory=None;loss=0
 for j in range(32):
  state,memory=m.step(history,u,memory);loss+=state.square().mean()+state.sum();history=advance(history,state)
 loss.backward();assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in m.parameters())
 checks.append(dict(kind=kind,parameters=sum(p.numel() for p in m.parameters()),exact_replay=True,backward32=True))
save('cuda-check.json',dict(passed=True,checks=checks))
'''+s[end:]
s=s.replace("for rotation in meta['rotations']:\n k=rotation['rotation'];", "jobs=[(rot,kind) for rot in meta['rotations'] for kind in P['arms']]\nfor k,(rotation,kind) in enumerate(jobs):\n ")
s=s.replace('model=Transition().to(device)','model=Transition(kind).to(device)')
s=s.replace("h=1 if epoch<=P['warmup_epochs'] else P['sequence_horizon_steps'];", "h=next(x['steps'] for x in reversed(P['horizon_curriculum']) if epoch>=x['first_epoch']);")
s=s.replace("hist=history_at(z,ids,js);loss=0.;normal=0.","hist=history_at(z,ids,js);memory=prefix_memory(model,z,ids,js);loss=0.;normal=0.")
s=s.replace("state=model(hist,external[ids,jj]);loss+=", "state,memory=model.step(hist,external[ids,jj],memory);loss+=")
s=s.replace("if epoch==P['warmup_epochs']+1:","if epoch in [21,41,61]:")
s=s.replace("elif epoch>P['warmup_epochs']:stale+=1", "elif epoch>61:stale+=1")
s=s.replace("dict(fold=k,epoch=epoch,model=", "dict(fold=k,rotation=rotation['rotation'],kind=kind,epoch=epoch,model=")
s=s.replace("epoch=best_epoch,fold=k)","epoch=best_epoch,fold=k,rotation=rotation['rotation'],kind=kind)")
s=s.replace("report=dict(fold=k,initial_hash=", "report=dict(fold=k,rotation=rotation['rotation'],kind=kind,initial_hash=")
s=s.replace('assert len(reports)==10','assert len(reports)==20')
s=s.replace("for rot in meta['rotations']:\n k=rot['rotation'];", "for k,(rot,kind) in enumerate(jobs):\n ")
s=s.replace("test=dict(fold=k,selected_epoch=", "test=dict(fold=k,rotation=rot['rotation'],kind=kind,selected_epoch=")
s=s.replace("folds=10))", "folds=20))")
# Horizon evaluation after selection gate: every valid origin, measured prefix, then self-fed.
pos=s.index("tests=[]")
s=s[:pos]+'''@torch.no_grad()
def horizon_metrics(model,z,ids,mean,std):
 result={}
 for h in P['evaluation_horizons']:
  ii=ids[:,None].expand(-1,91-h).flatten();jj=torch.arange(91-h,device=device).expand(len(ids),-1).flatten();parts=[];hold=[];truths=[]
  for off in range(0,len(ii),256):
   ci=ii[off:off+256];cj=jj[off:off+256];hist=history_at(z,ci,cj);memory=prefix_memory(model,z,ci,cj)
   for step in range(h):
    pred,memory=model.step(hist,external[ci,cj+step],memory);hist=advance(hist,pred)
   phys=torch.sinh(pred*std+mean)*scale;truth=raw[ci,cj+h];parts.append((phys-truth).abs());hold.append((raw[ci,cj]-truth).abs());truths.append(truth.abs())
  def aggregate(xs):return mean_groups(torch.cat(xs).reshape(len(ids),91-h,3).mean(1),ids).cpu().tolist()
  result[str(h)]=dict(steps=h,nominal_seconds=2*h,model_MAE=aggregate(parts),no_change_MAE=aggregate(hold),mean_absolute_truth=aggregate(truths),scope='All valid forecast origins; observed history through origin, predictions thereafter')
 return result
'''+s[pos:]
s=s.replace("metrics=result,persistence=baseline)", "metrics=result,persistence=baseline,horizons=horizon_metrics(model,z,ids,mean,std))")
(r/'worker.py').write_text(s)
print(r)
