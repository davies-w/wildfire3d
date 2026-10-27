"""Cloud CUDA-only fixed-feature head comparison; no base GRU training."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from pathlib import Path
import copy,hashlib,io,json,random,time
import numpy as np
import torch
from gas_head import GasHead
from gas_head_metrics import evaluate,acceptance
from runtime import upload
R=Path(__file__).resolve().parent;P=json.loads((R/'pilot-plan.json').read_text());C=json.loads((R/'candidate-plan.json').read_text());N=json.loads((R/'base-normalization.json').read_text());start=time.monotonic();assert torch.cuda.is_available(),'No local training';device='cuda';torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.manual_seed(3617);random.seed(3617);np.random.seed(3617)
a=np.load(R/'features.npz');x=torch.tensor(a['features'],device=device);base=torch.tensor(a['base_states'],device=device);raw=torch.tensor(a['truth'],device=device);times=torch.tensor(a['time'],device=device);config=torch.tensor(a['configuration'],device=device);labels=torch.tensor(a['activity_labels'],device=device);scales=torch.tensor(N['physical_encoding_scales'],device=device);std=torch.tensor(N['std'],device=device);train=torch.tensor(C['train_indices'],device=device);valid=torch.tensor(C['validation_indices'],device=device);initial=torch.load(R/'initial-head.pt',map_location=device,weights_only=False);assert not set(config[train].tolist())&set(config[valid].tolist());assert len(a['source_ids'])==C['train_histories']+C['validation_histories'];manifest={};folder=R/'results';folder.mkdir(exist_ok=True)
def save(name,value):
 b=json.dumps(value,allow_nan=False).encode();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def checkpoint(name,value):
 b=io.BytesIO();torch.save(value,b);payload=b.getvalue();(folder/name).write_bytes(payload);upload(name,payload);manifest[name]=hashlib.sha256(payload).hexdigest()
def statehash(state):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in state.values())).hexdigest()
def rngstate():return dict(torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all(),numpy=np.random.get_state(),python=random.getstate())
def restore_rng(r):torch.set_rng_state(r['torch'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in r['cuda']]);np.random.set_state(r['numpy']);random.setstate(r['python'])
initial_rng=rngstate()
def fresh():
 m=GasHead(initial['feature_mean'],initial['feature_std']).to(device);m.load_state_dict(initial['model']);o=torch.optim.AdamW(m.parameters(),lr=P['training']['learning_rate'],weight_decay=P['training']['weight_decay']);restore_rng(initial_rng);return m,o
active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5);weights=torch.zeros_like(base[:,:,2]);replicas=torch.ones(len(raw),device=device)
for i in train.tolist():
 ac=active[i];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);replicas[i]=int((config[train]==config[i]).sum());weights[i]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/replicas[i]
truth=raw[:,1:,2];peak=raw[:,:,2].amax(1).clamp_min(.01);startup=times[:,1:]<=32.2

def train_batch(m,o,ids,arm):
 m.train();gas=m(x[ids],base[ids,:,2]);encoded=((torch.asinh(gas/.01)-torch.asinh(truth[ids]/.01))/std[2]).square()/3;loss=(encoded*weights[ids]).mean()
 if arm=='peak_aware':
  predpeak=torch.maximum(gas.amax(1),raw[ids,0,2]);truepeak=raw[ids,:,2].amax(1);peak_loss=((predpeak-truepeak)/peak[ids]).square();trajectory=(((gas-truth[ids])/peak[ids,None]).square()*startup[ids]).sum(1)/startup[ids].sum(1).clamp_min(1);loss+=((.25*peak_loss+.1*trajectory)/replicas[ids]).mean()
 assert torch.isfinite(loss);o.zero_grad(set_to_none=True);loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters());torch.nn.utils.clip_grad_norm_(m.parameters(),1);o.step();return float(loss.detach())
@torch.no_grad()
def score(m,ids):
 m.eval();gas=m(x[ids],base[ids,:,2]);r=evaluate(gas,base[ids],raw[ids],times[ids],config[ids],labels[ids],scales,std);nonzero=base[ids,:,2]!=0;factor=gas[nonzero]/base[ids,:,2][nonzero];r['factor_fraction_near_bounds']=float(((factor<.505)|(factor>1.995)).float().mean());return r
replays=[]
for arm in ['encoded_only','peak_aware']:
 m,o=fresh();ids=train[:128];train_batch(m,o,ids,arm);snap=copy.deepcopy(dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate()));assert snap['optimizer']['state'];train_batch(m,o,ids,arm);expected=copy.deepcopy(m.state_dict());expected_opt=copy.deepcopy(o.state_dict());m.load_state_dict(snap['model']);o.load_state_dict(copy.deepcopy(snap['optimizer']));restore_rng(snap['rng']);train_batch(m,o,ids,arm);assert all(torch.equal(expected[k],v) for k,v in m.state_dict().items())
 for key,value in o.state_dict()['state'].items():
  for name,v in value.items():assert torch.equal(v,expected_opt['state'][key][name]) if torch.is_tensor(v) else v==expected_opt['state'][key][name]
 replays.append(dict(arm=arm,next_update_bitwise_equal=True,nonempty_optimizer=True))
save('optimizer-replay.json',dict(passed=True,arms=replays));m,_=fresh();baseline=score(m,valid);save('baseline.json',baseline);selections=[];soft=P['budget_plan']['training_soft_cap_s']
for arm in ['encoded_only','peak_aware']:
 m,o=fresh();best_state=copy.deepcopy(m.state_dict());best_row=dict(epoch=0,validation=baseline);history=[best_row];best=baseline['objective'];best_epoch=0
 for ep in range(1,P['training']['epochs_per_arm']+1):
  order=torch.tensor(np.random.default_rng(3617+ep).permutation(len(train)),device=device);total=0.;batches=0
  for cursor in range(0,len(train),128):
   if time.monotonic()-start>=soft:
    checkpoint(f'{arm}-partial.pt',dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate(),epoch=ep,batch_cursor=cursor,permutation=order,training_total=total,training_batches=batches,history=history,best_state=best_state,best_epoch=best_epoch,best_row=best_row));save('incomplete.json',dict(experiment_complete=False,reason='soft_deadline',arm=arm,epoch=ep,batch_cursor=cursor,automatic_retry=False));raise SystemExit(0)
   total+=train_batch(m,o,train[order[cursor:cursor+128]],arm);batches+=1
  row=None
  if ep%10==0:
   row=dict(epoch=ep,training_loss=total/batches,validation=score(m,valid),train=score(m,train),elapsed_s=time.monotonic()-start);history.append(row);save(f'{arm}-epoch{ep:03}.json',row)
   if row['validation']['objective']<best:best=row['validation']['objective'];best_epoch=ep;best_row=row;best_state=copy.deepcopy(m.state_dict())
  checkpoint(f'{arm}-epoch{ep:03}.pt',dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate(),epoch=ep,batch_cursor=len(train),history=history,best_state=best_state,best_epoch=best_epoch,best_row=best_row))
 checkpoint(f'{arm}-selected.pt',dict(model=best_state,epoch=best_epoch,arm=arm));selection=dict(arm=arm,epoch=best_epoch,model_sha256=statehash(best_state),row=best_row);save(f'{arm}-selection.json',selection);selections.append(selection)
save('selection-freeze.json',dict(arms=selections,test_evaluated=False,selection=P['training']['selection']));primary=selections[1]['row']['validation'];checks=acceptance(baseline,primary,P['acceptance_all_required'],scales.tolist());save('comparison.json',dict(passed=all(checks.values()),checks=checks,baseline=baseline,primary=primary,selections=selections,test_evaluated=False,scope=P['scope']));save('complete.json',dict(passed=True,arms_completed=2,epochs_per_arm=P['training']['epochs_per_arm'],test_evaluated=False,repair_acceptance_passed=all(checks.values()),manifest=copy.deepcopy(manifest)))
