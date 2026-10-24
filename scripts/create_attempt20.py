"""Create matched thermal-state diagnostic; no launch."""
from pathlib import Path
import json,shutil,yaml
repo=Path(__file__).resolve().parents[1];o=repo/'experiments/35_surrogate_diagnostics/attempt18';r=o.parent/'attempt20';r.mkdir(exist_ok=False);(r/'results').mkdir();(r/'data/resume').mkdir(parents=True)
for n in ['cloud.py','runtime.py','launch.py','collect.py','prepare_pilot.py','finish_run.py','finalize_archive.py','validate_transport.py']:
 s=(o/n).read_text().replace('attempt18','attempt20').replace('memory35-18','thermal35-20').replace('gpu35-memory18','gpu35-thermal20').replace('exp35-memory18','exp35-thermal20')
 if n=='launch.py':
  s=s.replace("  assert read('results/resume-preflight.json')['passed']\n",'').replace("  assert read('results/resume-proof.json')['model15_epoch']==373\n",'')
  s=s.replace('+3<=','+8<=').replace('+3,2)','+8,2)').replace('allowance_usd=3','allowance_usd=8').replace('compute_allowance_usd=2.2','compute_allowance_usd=6').replace('ancillary_cleanup_allowance_usd=.8','ancillary_cleanup_allowance_usd=2').replace('expected_usd=[.5,1.5]','expected_usd=[2,4.5]')
 if n=='prepare_pilot.py':
  s=s.replace("'+ 12600'","'+ 23400'").replace("'+ 11100'","'+ 21900'").replace("'10800s'","'21600s'").replace('proposed_new_cap_usd=3','proposed_new_cap_usd=8').replace('estimated_usd=[.5,1.5]','estimated_usd=[2,4.5]').replace('task_deadline_s=10800','task_deadline_s=21600').replace('vm_age_limit_s=11100','vm_age_limit_s=21900').replace('absolute_deadline_s=12600','absolute_deadline_s=23400')
 (r/n).write_text(s)
p=json.loads((o/'coverage-plan.json').read_text());p.pop('continuation',None);p.update(experiment='Matched GRU three-state versus thermal-proxy fourth-state',arms=['control','thermal'],state_features=4,input_features=25,architecture='Both GRU25->32->4; control masks fourth channel to zero in history and readout, effective21inputs/3outputs; thermal25inputs/4outputs. Same initialized parameter tensors.',selection='Minimum original-three-state autonomous validation MSE; extra thermal state excluded from selection score. All20 selections frozen before test.',training_balance=p['training_balance'],thermal_loss='Original three-channel MSE plus one-third normalized thermal squared error; control thermal target/readout zero. Identical original-channel weights. This tests added observed thermal history AND thermal prediction supervision, not an isolated causal intervention.')
p['budget']=dict(expected_usd=[2,4.5],maximum_allowance_usd=8,task_seconds=21600,vm_seconds=21900,absolute_seconds=23400,soft_seconds=20400,queue_seconds=1200)
(r/'coverage-plan.json').write_text(json.dumps(p,indent=2))
(r/'prepare.py').write_text('''from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parent;a=np.load(R.parent/'attempt18/data/sequences.npz');h=np.load(R.parent/'attempt19/data/thermal_candidates.npz');assert np.array_equal(a['time'],h['time']);data={k:a[k] for k in a.files};data['state']=np.concatenate([a['state'],h['thermal'][:,:,None]],-1).astype('float32');assert data['state'].shape==(520,91,4);np.savez_compressed(R/'data/sequences.npz',**data)
s=json.loads((R.parent/'attempt18/schema.json').read_text());s['state_names']=s['state_names']+['surface_heating_index_K'];s['physical_encoding_scales']=s['physical_encoding_scales']+[100.];s['model_input_shape']=[None,25];s['model_output_shape']=[None,4];s['comparison']='Three-state GRU control vs additional surface-heating index (not thermal energy J); fourth channel masked for control; same grouped rotations.';(R/'schema.json').write_text(json.dumps(s,indent=2))
''')
(r/'model.py').write_text('''"""Same-size GRUs, only thermal input/output enabled versus masked control."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,kind='control'):
  super().__init__();assert kind in ['control','thermal'];self.kind=kind;self.cell=nn.GRU(25,32,batch_first=True);self.head=nn.Linear(32,4);nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
 def inputs(self,history,external):
  if self.kind=='control':history=history*history.new_tensor([1,1,1,0])
  return torch.cat([history.flatten(1),external],-1)
 def step(self,history,external,memory=None):
  x=self.inputs(history,external);sequence,hidden=self.cell(x[:,None],None if memory is None else memory[None]);memory=hidden[0];state=history[:,-1]+self.head(memory)*external[:,-1:]
  if self.kind=='control':state=state*state.new_tensor([1,1,1,0])
  return state,memory
 def forward(self,history,external):return self.step(history,external)[0]
'''+ '\ndef normalize_fit'+(o/'model.py').read_text().split('def normalize_fit',1)[1])
s=(o/'worker.py').read_text();s=s.replace("raw=torch.tensor(a['state'],device=device)","raw_full=torch.tensor(a['state'],device=device);raw=raw_full.clone()")
s=s.replace("def objective(pred,target):return (pred-target).square().mean(-1)","def objective(pred,target):return (pred[...,:3]-target[...,:3]).square().mean(-1)\ndef training_objective(pred,target):return (pred-target).square().sum(-1)/3")
start=s.index('@torch.no_grad()\ndef prefix_memory');end=s.index('@torch.no_grad()\ndef evaluate',start)
s=s[:start]+'''@torch.no_grad()
def prefix_memory(model,z,ids,js):
 memory=torch.zeros(len(ids),32,device=z.device);length=int(js.max())
 if length==0:return memory
 ii=ids[:,None].expand(-1,length).flatten();jj=torch.arange(length,device=z.device).expand(len(ids),-1).flatten()
 history=history_at(z,ii,jj);inputs=model.inputs(history,external[ii,jj]).reshape(len(ids),length,25)
 output,_=model.cell(inputs);memory=output[torch.arange(len(ids),device=z.device),(js-1).clamp_min(0)]
 return torch.where((js>0)[:,None],memory,torch.zeros_like(memory))
@torch.no_grad()
def predictions(model,z,ids,rollout):
 history=history_at(z,ids,torch.zeros_like(ids));out=[];memory=None
 for j in range(90):
  if not rollout:history=history_at(z,ids,torch.full_like(ids,j))
  state,memory=model.step(history,external[ids,j],memory);out.append(state);history=advance(history,state)
 return torch.stack(out,1)
'''+s[end:]
s=s.replace("(m.head if kind=='gru' else m.net[-1])","m.head").replace('torch.zeros(4,4,3','torch.zeros(4,4,4').replace("if kind=='gru':","if kind in P['arms']:").replace('torch.randn(4,12,21','torch.randn(4,12,25')
start=s.index('# Exercise the actual saved checkpoint');end=s.index('reports=[]',start);s=s[:start]+s[end:]
s=s.replace(" train=torch.tensor(rotation['train'],device=device)"," raw=raw_full.clone()\n if kind=='control':raw[:,:,3]=0\n train=torch.tensor(rotation['train'],device=device)")
s=s.replace('loss+=(objective(state,z[ids,jj+1])','loss+=(training_objective(state,z[ids,jj+1])')
s=s.replace('reshape(len(ids),91-h,3)','reshape(len(ids),91-h,4)')
s=s.replace(" ck=torch.load(folder/f'fold{k:02}-selected.pt'", " raw=raw_full.clone()\n if kind=='control':raw[:,:,3]=0\n ck=torch.load(folder/f'fold{k:02}-selected.pt'")
# Save validation traces too; never choose thermal candidates using tests.
needle="buf=io.BytesIO();np.savez_compressed(buf,case_indices=ids.cpu().numpy()"
pos=s.index(' '+needle)
s=s[:pos]+''' for split,split_ids in [('validation',torch.tensor(rot['validation'],device=device))]:
  buf=io.BytesIO();np.savez_compressed(buf,case_indices=split_ids.cpu().numpy(),times=times[split_ids].cpu().numpy(),normalized_rollout=predictions(model,z,split_ids,True).cpu().numpy(),mean=mean.cpu().numpy(),std=std.cpu().numpy(),physical_scales=scale.cpu().numpy());data=buf.getvalue();name=f'fold{k:02}-{split}-predictions.npz';(folder/name).write_bytes(data);upload(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
'''+s[pos:]
s=s.replace('baseline=evaluate(Transition().to(device),z','baseline=evaluate(Transition(kind).to(device),z')
s=s.replace("scope='Water/dryfuel/fuel-gas release only; char inert; no gas combustion or heat prediction; reshuffled data not historically pristine'", "scope='Matched thermal surface-heating proxy fourth-state; not stored energy J. Original three-state validation selection; previously examined grouped data.'")
# Check actual nonempty optimizer/RNG restore on GPU after first completed epoch, without another optimization.
needle="  checkpoint(f'fold{k:02}-epoch{epoch:03}.pt',pack())"
s=s.replace(needle,needle+'''
  if epoch==1:
   probe=pack();buf=io.BytesIO();torch.save(probe,buf);buf.seek(0);probe=torch.load(buf,map_location=device,weights_only=False);mm=Transition(kind).to(device);mm.load_state_dict(probe['model']);oo=torch.optim.AdamW(mm.parameters(),lr=P['learning_rate']);oo.load_state_dict(probe['optimizer']);assert len(oo.state)>0
   xx=history_at(z,train[:4],torch.zeros(4,dtype=torch.long,device=device));uu=external[train[:4],0];assert torch.equal(model(xx,uu),mm(xx,uu));restore_rng(probe['rng']);aa=torch.rand(8,device=device);restore_rng(probe['rng']);assert torch.equal(aa,torch.rand(8,device=device));restore_rng(probe['rng']);save(f'fold{k:02}-checkpoint-replay.json',dict(passed=True,epoch=1,optimizer_nonempty=True));del mm,oo,probe
''')
(r/'worker.py').write_text(s)
v=(o/'validate.py').read_text().replace('(520,91,3)','(520,91,4)').replace("'objective','history_at'","'objective','training_objective','history_at'").replace("for kind in ['mlp','gru']:","for kind in ['control','thermal']:\n if kind=='control':\n  armraw=raw.clone();armraw[:,:,3]=0\n else:armraw=raw.clone()\n mean,std=normalize_fit(armraw,ids,config,scale);z=(torch.asinh(armraw/scale)-mean)/std;ns['raw']=armraw").replace("head=m.head if kind=='gru' else m.net[-1]","head=m.head").replace("if kind=='gru':","if kind in ['control','thermal']:")
v=v.replace("checks=[]","checks=[]\ntorch.manual_seed(3516);ma=Transition('control');torch.manual_seed(3516);mb=Transition('thermal');assert all(torch.equal(x,y) for x,y in zip(ma.state_dict().values(),mb.state_dict().values()))")
(r/'validate.py').write_text(v)
an=(o/'analyze.py').read_text().replace("['mlp','gru']","['control','thermal']");(r/'analyze.py').write_text(an)
d=yaml.safe_load((o/'dvc.yaml').read_text());d['stages']['prepare_data']={'cmd':'../../../.venv/bin/python prepare.py','deps':['prepare.py','../attempt18/data/sequences.npz','../attempt18/schema.json','../attempt19/data/thermal_candidates.npz'],'outs':['data/sequences.npz',{'schema.json':{'cache':False}}]}
d['stages']['package']['cmd']='../../../.venv/bin/python validate.py && ../../../.venv/bin/python validate_transport.py && ../../../.venv/bin/python prepare_pilot.py';d['stages']['package']['deps']=[x for x in d['stages']['package']['deps'] if x not in ['data/resume','results/resume-proof.json','validate_resume.py']];d['stages']['package']['metrics']=[{'results/transport-preflight.json':{'cache':False}}];d['stages'].pop('validation_burn_audit',None);(r/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
