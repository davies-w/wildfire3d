"""Cloud-only minimal-state sequence learning; single gated selection frozen before test."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from pathlib import Path
import json,io,time,hashlib,random
import numpy as np
import torch
import torch.nn.functional as F
from model import Transition,normalize_fit
from runtime import upload
from objective import interval_error,sequence_score
R=Path(__file__).resolve().parent;P=json.loads((R/'coverage-plan.json').read_text());meta=json.loads((R/'schema.json').read_text());start=time.monotonic()
torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'
device='cuda';torch.manual_seed(3516);np.random.seed(3516);random.seed(3516)
a=np.load(R/'data/sequences.npz');raw_full=torch.tensor(a['state'],device=device);raw=raw_full.clone();times=torch.tensor(a['time'],device=device);geom=torch.tensor(a['geometry'],device=device);config=torch.tensor(a['configuration'],device=device);scale=torch.tensor(meta['physical_encoding_scales'],device=device)
ranges=raw_full.amax(1)-raw_full.amin(1)
assert bool((ranges>0).all()),'Undefined zero-range feature'
dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt
external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales'],device=device)
active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5)
activity_labels=torch.tensor(a['activity_labels'],device=device)
gate_targets=torch.tensor(a['gate_targets'],device=device);gate_supervised=torch.tensor(a['gate_supervised'],device=device)
assert external.shape==(2080,90,9)
assert len(meta['rotations'])==1
assert all(len(set(meta['cases'][i]['fold'] for i in rot['train']))==8 for rot in meta['rotations'])
folder=R/'results';folder.mkdir(exist_ok=True);manifest={}
def save(name,obj):
 b=json.dumps(obj,allow_nan=False).encode();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def checkpoint(name,obj):
 f=io.BytesIO();torch.save(obj,f);b=f.getvalue();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def statehash(state):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in state.values())).hexdigest()
def mean_groups(value,ids):
 # Equal configuration weight: each history contributes inverse replica count.
 _,inverse,counts=torch.unique(config[ids],return_inverse=True,return_counts=True)
 weights=counts[inverse].to(value.dtype).reciprocal()
 return (value*weights.reshape((-1,)+(1,)*(value.ndim-1))).sum(0)/len(counts)
def objective(pred,target):return (pred[...,:3]-target[...,:3]).square().mean(-1)
def training_objective(pred,target):return (pred-target).square().sum(-1)/3
def history_at(z,ids,js):return z[ids[:,None],(js[:,None]+torch.arange(-7,1,device=z.device)[None,:]).clamp_min(0)]
def advance(history,state):return torch.cat([history[:,1:],state[:,None]],1)
def phase_mae(errors,phase,ids):
 den=phase.sum(1);keep=den>0
 return mean_groups((errors*phase[:,:,None]).sum(1)[keep]/den[keep,None],ids[keep]).cpu().tolist() if bool(keep.any()) else None
@torch.no_grad()
def prefix_memory(model,z,ids,js):
 memory=torch.zeros(len(ids),64,device=z.device);length=int(js.max())
 if length==0:return memory
 ii=ids[:,None].expand(-1,length).flatten();jj=torch.arange(length,device=z.device).expand(len(ids),-1).flatten()
 history=history_at(z,ii,jj);inputs=model.inputs(history,external[ii,jj]).reshape(len(ids),length,41)
 output,_=model.cell(inputs);memory=output[torch.arange(len(ids),device=z.device),(js-1).clamp_min(0)]
 return torch.where((js>0)[:,None],memory,torch.zeros_like(memory))
@torch.no_grad()
def predictions(model,z,ids,rollout):
 history=history_at(z,ids,torch.zeros_like(ids));out=[];memory=None
 for j in range(90):
  if not rollout:history=history_at(z,ids,torch.full_like(ids,j))
  state,memory=model.step(history,external[ids,j],memory);out.append(state);history=advance(history,state)
 return torch.stack(out,1)
@torch.no_grad()
def evaluate(model,z,ids,mean,std,details=False):
 model.eval();out={}
 for mode in ['one_step','rollout']:
  pred=predictions(model,z,ids,mode=='rollout');err=objective(pred,z[ids,1:]).mean(1);phys=torch.sinh(pred*std+mean)*scale
  legacy=err
  curves=torch.cat([raw[ids,:1],phys],1);integrals=sequence_score(curves,raw[ids],times[ids],ranges[ids]);err=integrals.mean(-1)
  finite=bool(torch.isfinite(phys).all() and torch.isfinite(err).all());entry=dict(objective=float(mean_groups(err,ids)) if finite else 1e30,finite=finite)
  if not finite:out[mode]=entry;continue
  entry['integral_error_percent_by_feature']=(100*mean_groups(integrals,ids)).cpu().tolist();entry['legacy_three_state_normalized_mse']=float(mean_groups(legacy,ids))
  errors=(phys-raw[ids,1:]).abs();mae=errors.mean(1);entry['physical_MAE_by_feature']=mean_groups(mae,ids).cpu().tolist()
  entry['physical_MAE_by_window']={name:phase_mae(errors,p,ids) for name,p in [('ignition',times[ids,1:]<=20),('post_source_to90',(times[ids,1:]>20)&(times[ids,1:]<=90)),('after90',times[ids,1:]>90),('active',active[ids]),('quiet',~active[ids])]}
  curve=torch.cat([raw[ids,0:1],phys],1);change=curve[:,1:,:2]-curve[:,:-1,:2]
  entry['minimum_by_feature']=phys.amin((0,1)).cpu().tolist();entry['negative_fraction_by_feature']=mean_groups((phys<0).float().mean(1),ids).cpu().tolist();entry['negative_magnitude_mean_by_feature']=mean_groups((-phys).clamp_min(0).mean(1),ids).cpu().tolist();entry['mass_increase_fraction']=mean_groups((change>1e-6).float().mean(1),ids).cpu().tolist();entry['mass_increase_total_kg']=mean_groups(change.clamp_min(0).sum(1),ids).cpu().tolist()
  integral=(.5*(curve[:,1:,2]+curve[:,:-1,2])*dt[ids]).sum(1);truthintegral=(.5*(raw[ids,1:,2]+raw[ids,:-1,2])*dt[ids]).sum(1)
  entry['released_fuel_integral_MAE_kg']=float(mean_groups((integral-truthintegral).abs(),ids))
  peak=curve[:,:,2].max(1);truthpeak=raw[ids,:,2].max(1);entry['peak_release_MAE_kg_s']=float(mean_groups((peak.values-truthpeak.values).abs(),ids));entry['peak_time_MAE_s']=float(mean_groups((times[ids,peak.indices]-times[ids,truthpeak.indices]).abs(),ids))
  positive=curve[:,:,2].clamp_min(0);cumulative=torch.cat([torch.zeros(len(ids),1,device=device),torch.cumsum(((positive[:,1:]+positive[:,:-1])*.5*dt[ids]).cpu(),1).to(device)],1);ends=torch.arange(1,91,device=device);begins=(ends-5).clamp_min(0);elapsed=times[ids][:,ends]-times[ids][:,begins];release_rate=(cumulative[:,ends]-cumulative[:,begins])/.75/raw[ids,0,1,None]/elapsed;predactive=release_rate>=1e-4;truthactive=activity_labels[ids]==1
  def ratio_per_config(num,den):
   good=den>0
   return float(mean_groups((num[good]/den[good]),ids[good])) if bool(good.any()) else None
  entry['release_activity_v1']=dict(missed_active_fraction=ratio_per_config((truthactive&~predactive).sum(1),truthactive.sum(1)),false_active_fraction=ratio_per_config((~truthactive&predactive).sum(1),(~truthactive).sum(1)),scope='Trailing10s integrated fuel-release threshold, true activity from frozen scorecard; smoothing lag applies.')
  if details:entry['cases']=[dict(case=meta['cases'][n]['case'],configuration=int(config[n]),objective=float(err[j]),physical_MAE_by_feature=mae[j].cpu().tolist(),released_fuel_integral_kg=float(integral[j]),truth_released_fuel_kg=float(truthintegral[j])) for j,n in enumerate(ids.tolist())]
  out[mode]=entry
 return out

def rngstate():return dict(torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all(),numpy=np.random.get_state(),python=random.getstate())
def restore_rng(x):torch.set_rng_state(x['torch'].cpu());torch.cuda.set_rng_state_all([state.cpu() for state in x['cuda']]);np.random.set_state(x['numpy']);random.setstate(x['python'])
checks=[]
for kind in P['arms']:
 m=Transition(kind).to(device);m.train();m.shared[-1].eval()
 with torch.no_grad():
  m.head.weight.fill_(.001)
 b=torch.zeros(4,8,4,device=device);u=external[:4,0];q=m(b,u);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition(kind).to(device);m2.train();m2.shared[-1].eval();m2.load_state_dict(torch.load(buf,weights_only=False,map_location=device));assert torch.equal(q,m2(b,u));q.sum().backward();g=[None if p.grad is None else p.grad.clone() for p in m.parameters()];m.zero_grad();m(b,u).sum().backward();assert all((v is None and p.grad is None) or (v is not None and p.grad is not None and torch.equal(v,p.grad)) for v,p in zip(g,m.parameters()))
 m.zero_grad();history=b;memory=None;loss=0
 for j in range(32):
  state,memory=m.step(history,u,memory);loss+=state.square().mean()+state.sum();history=advance(history,state)
 loss.backward();assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in m.parameters())
 if kind in P['arms']:
  xx=torch.randn(4,12,41,device=device);whole,_=m.cell(xx);mem=None;seq=[]
  for j in range(12):
   yy,mem=m.cell(xx[:,j:j+1],mem);seq.append(yy)
  assert torch.allclose(torch.cat(seq,1),whole,atol=2e-6,rtol=2e-5),'CUDA prefix equivalence'
 checks.append(dict(kind=kind,parameters=sum(p.numel() for p in m.parameters()),exact_replay=True,backward32=True,mode="training_gru_dropout_disabled"))
save('cuda-check.json',dict(passed=True,checks=checks))
# Exercise the complete reporting path for both arms before any optimizer/fitting.
evaluation_checks=[]
for check_kind in P['arms']:
 ids=torch.tensor(meta['rotations'][0]['validation'],device=device)
 train_ids=torch.tensor(meta['rotations'][0]['train'],device=device)
 cm,cs=normalize_fit(raw,train_ids,config,scale);cz=(torch.asinh(raw/scale)-cm)/cs
 check_model=Transition(check_kind).to(device);check_model.set_normalization(cm,cs)
 result=evaluate(check_model,cz,ids,cm,cs,True)
 assert all(result[mode]['finite'] for mode in ['one_step','rollout'])
 evaluation_checks.append(dict(kind=check_kind,passed=True,modes=list(result)))
save('evaluation-cloud-check.json',dict(passed=True,checks=evaluation_checks))

# Preserve original completed epochs in the continuation manifest, byte-for-byte.
for prior in sorted((R/'data/resume/archive').glob('*')):
 data=prior.read_bytes();(folder/prior.name).write_bytes(data);upload(prior.name,data);manifest[prior.name]=hashlib.sha256(data).hexdigest()
reports=[]
jobs=[(rot,kind) for rot in meta['rotations'] for kind in P['arms']]
for k,(rotation,kind) in enumerate(jobs):
 previous=R/'data/resume'/f'fold{k:02}-report.json'
 if previous.exists():
  old=json.loads(previous.read_text());assert old['fold']==k
  ck=torch.load(R/'data/resume'/f'fold{k:02}-selected.pt',map_location='cpu',weights_only=False);checkpoint(f'fold{k:02}-selected.pt',ck);save(f'fold{k:02}-report.json',old);reports.append(old);continue
 raw=raw_full.clone()

 train=torch.tensor(rotation['train'],device=device);valid=torch.tensor(rotation['validation'],device=device)
 torch.manual_seed(3516);model=Transition(kind).to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=P['learning_rate'],weight_decay=1e-4);mean,std=normalize_fit(raw,train,config,scale);model.set_normalization(mean,std);z=(torch.asinh(raw/scale)-mean)/std
 # All windows have equal configuration weight; no old active/quiet weights.
 replica_weights=torch.zeros(2080,device=device)
 for n in train.tolist():replica_weights[n]=1/int((config[train]==config[n]).sum())
 best=1e30;significant=1e30;stale=0;history=[];best_state=None;best_epoch=0;epoch=0;globalstep=0;resume_start=1;initial_hash=statehash(dict(model.named_parameters()))
 resume=R/'data/resume'/f'fold{k:02}.pt'
 if resume.exists():
  ck=torch.load(resume,map_location=device,weights_only=False);assert ck['fold']==k and ck['schema_hash']==hashlib.sha256((R/'schema.json').read_bytes()).hexdigest();model.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer']);history=ck['history'];best=ck['best'];significant=ck['significant'];stale=ck['stale'];best_state=ck['best_state'];best_epoch=ck['best_epoch'];globalstep=ck['globalstep'];resume_start=ck['epoch']+1;restore_rng(ck['rng'])
 def pack():return dict(fold=k,rotation=rotation['rotation'],kind=kind,epoch=epoch,model=model.state_dict(),optimizer=optimizer.state_dict(),mean=mean,std=std,best=best,significant=significant,stale=stale,best_state=best_state,best_epoch=best_epoch,history=history,globalstep=globalstep,rng=rngstate(),schema_hash=hashlib.sha256((R/'schema.json').read_bytes()).hexdigest(),checkpoint_boundary='completed epoch; next epoch order deterministic')
 if not history:
  save(f'fold{k:02}-baseline.json',evaluate(model,z,valid,mean,std,True));history.append(dict(epoch=0,train=evaluate(model,z,train,mean,std),validation=evaluate(model,z,valid,mean,std)))
 stop='epoch_cap_not_convergence'
 for epoch in range(resume_start,P['epochs_max']+1):
  if time.monotonic()-start>int(os.environ['TRAINING_SOFT_SECONDS']):
   epoch-=1;checkpoint(f'fold{k:02}-deadline.pt',pack());save('partial.json',dict(reason='soft_deadline',completed_folds=len(reports),active_fold=k,epoch=epoch));raise RuntimeError('Deadline checkpoint retained; no automatic continuation')
  h=next(x['steps'] for x in reversed(P['horizon_curriculum']) if epoch>=x['first_epoch']);windows=[(int(n),j) for n in train.tolist() for j in range(0,91-h)];order=np.random.default_rng(3516+rotation['rotation']*10000+epoch).permutation(len(windows));model.train();total=0.;batches=0
  for off in range(0,len(windows),P['batch_windows']):
   batch=[windows[i] for i in order[off:off+P['batch_windows']]];ids=torch.tensor([n for n,j in batch],device=device);js=torch.tensor([j for n,j in batch],device=device);hist=history_at(z,ids,js);memory=prefix_memory(model,z,ids,js);loss=0.;normal=0.
   left_error=torch.zeros(len(ids),4,device=device);state_integral=torch.zeros(len(ids),4,device=device);gate_integral=torch.zeros(len(ids),device=device)
   duration=times[ids,js+h]-times[ids,js]
   for step in range(h):
    jj=js+step;state,memory=model.step(hist,external[ids,jj],memory)
    physical=torch.sinh(state*std+mean)*scale;right_error=physical-raw[ids,jj+1]
    state_integral=state_integral+interval_error(left_error,right_error)*dt[ids,jj,None]
    supervised=gate_supervised[ids,jj];bce=F.binary_cross_entropy_with_logits(model.last_gate_logits,gate_targets[ids,jj],reduction='none')
    gate_integral=gate_integral+dt[ids,jj]*(bce*supervised).sum(-1)/supervised.sum(-1).clamp_min(1)
    left_error=right_error;hist=advance(hist,state)
   state_per_window=(state_integral/(duration[:,None]*ranges[ids])).mean(-1)
   gate_per_window=gate_integral/duration
   loss=((state_per_window+P['gate_loss_weight']*gate_per_window)*replica_weights[ids]).sum()/replica_weights[ids].sum();assert bool(torch.isfinite(loss)),f'Nonfinite fold{k} epoch{epoch}';optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step();globalstep+=1;total+=float(loss);batches+=1
  tr=evaluate(model,z,train,mean,std);va=evaluate(model,z,valid,mean,std);score=va['rollout']['objective'];row=dict(epoch=epoch,horizon=h,optimizer_updates=globalstep,training_window_objective=total/batches,train=tr,validation=va);history.append(row)
  if best_state is None or score<best:best=score;best_epoch=epoch;best_state={n:v.detach().cpu().clone() for n,v in model.state_dict().items()}
  if epoch in [s['first_epoch'] for s in P['horizon_curriculum']][1:]:significant=score;stale=0
  elif score<significant-max(P['improvement_absolute'],P['improvement_relative']*abs(significant)):significant=score;stale=0
  elif epoch>P['horizon_curriculum'][-1]['first_epoch']:stale+=1
  save(f'fold{k:02}-epoch{epoch:03}.json',row)
  checkpoint(f'fold{k:02}-epoch{epoch:03}.pt',pack())
  if epoch==1:
   probe=pack();buf=io.BytesIO();torch.save(probe,buf);buf.seek(0);probe=torch.load(buf,map_location=device,weights_only=False);mm=Transition(kind).to(device);mm.eval();mm.load_state_dict(probe['model']);oo=torch.optim.AdamW(mm.parameters(),lr=P['learning_rate']);oo.load_state_dict(probe['optimizer']);assert len(oo.state)>0
   xx=history_at(z,train[:4],torch.zeros(4,dtype=torch.long,device=device));uu=external[train[:4],0];assert torch.equal(model(xx,uu),mm(xx,uu));restore_rng(probe['rng']);aa=torch.rand(8,device=device);restore_rng(probe['rng']);assert torch.equal(aa,torch.rand(8,device=device));restore_rng(probe['rng']);save(f'fold{k:02}-checkpoint-replay.json',dict(passed=True,epoch=1,optimizer_nonempty=True,eval_forward_bitwise=True,rng_restored=True,inherited=False));del mm,oo,probe

  print('FOLD',k,'EPOCH',epoch,'TRAIN',tr['rollout']['objective'],'VAL',score,flush=True)
  if epoch>=P['minimum_epochs'] and stale>=P['patience_epochs']:stop='validation_patience';break
 assert best_state is not None
 checkpoint(f'fold{k:02}-final.pt',pack());final=dict(train=evaluate(model,z,train,mean,std,True),validation=evaluate(model,z,valid,mean,std,True));model.load_state_dict(best_state)
 checkpoint(f'fold{k:02}-selected.pt',dict(model=best_state,mean=mean.cpu(),std=std.cpu(),epoch=best_epoch,fold=k,rotation=rotation['rotation'],kind=kind))
 report=dict(fold=k,rotation=rotation['rotation'],kind=kind,training_fold_count=8,initial_hash=initial_hash,epochs=epoch,selected_epoch=best_epoch,stop_reason=stop,history=history,final=final,selected=dict(train=evaluate(model,z,train,mean,std,True),validation=evaluate(model,z,valid,mean,std,True)))
 save(f'fold{k:02}-report.json',report);reports.append(report)
assert len(reports)==1
save('selection-freeze.json',dict(selected=[dict(fold=r['fold'],epoch=r['selected_epoch']) for r in reports],test_not_evaluated_yet=True))
@torch.no_grad()
def horizon_metrics(model,z,ids,mean,std):
 result={}
 for h in P['evaluation_horizons']:
  ii=ids[:,None].expand(-1,91-h).flatten();jj=torch.arange(91-h,device=device).expand(len(ids),-1).flatten();parts=[];hold=[];truths=[];forecast_parts=[]
  for off in range(0,len(ii),256):
   ci=ii[off:off+256];cj=jj[off:off+256];hist=history_at(z,ci,cj);memory=prefix_memory(model,z,ci,cj)
   for step in range(h):
    pred,memory=model.step(hist,external[ci,cj+step],memory);hist=advance(hist,pred)
   phys=torch.sinh(pred*std+mean)*scale;truth=raw[ci,cj+h];parts.append((phys-truth).abs());hold.append((raw[ci,cj]-truth).abs());truths.append(truth.abs());forecast_parts.append(phys)
  def aggregate(xs):return mean_groups(torch.cat(xs).reshape(len(ids),91-h,4).mean(1),ids).cpu().tolist()
  errors=torch.cat(parts).reshape(len(ids),91-h,4);hold_errors=torch.cat(hold).reshape(len(ids),91-h,4)
  finite=bool(torch.isfinite(errors).all())
  windows={'ignition':times[ids,h:]<=20,'post_source_to90':(times[ids,h:]>20)&(times[ids,h:]<=90),'after90':times[ids,h:]>90,'active':active[ids,h-1:],'quiet':~active[ids,h-1:]}
  v1=activity_labels[ids].unfold(1,h,1);va=((v1==1)|(v1==2)).all(-1);vq=(v1==0).all(-1);vw=(v1==3).all(-1);vm={'active':va,'quiet':vq,'weak':vw,'transition':~(va|vq|vw)}
  windows.update({'v1_'+w:m for w,m in vm.items()})
  if P.get('save_forecasts',True):
   buf=io.BytesIO();np.savez_compressed(buf,case_indices=ids.cpu().numpy(),predicted_physical=torch.cat(forecast_parts).reshape(len(ids),91-h,4).cpu().numpy());data=buf.getvalue();name=f'fold{k:02}-horizon{h:02}-predictions.npz';(folder/name).write_bytes(data);upload(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
  result[str(h)]=dict(steps=h,nominal_seconds=2*h,finite=finite,model_MAE=aggregate(parts) if finite else None,no_change_MAE=aggregate(hold),mean_absolute_truth=aggregate(truths),model_windows={w:phase_mae(errors,m,ids) if finite else None for w,m in windows.items()},no_change_windows={w:phase_mae(hold_errors,m,ids) for w,m in windows.items()},truth_windows={w:phase_mae(torch.cat(truths).reshape(len(ids),91-h,4),m,ids) for w,m in windows.items()},scope='All valid forecast origins; observed history through origin, predictions thereafter; windows by endpoint')
 return result
tests=[]
for k,(rot,kind) in enumerate(jobs):
 raw=raw_full.clone()

 ck=torch.load(folder/f'fold{k:02}-selected.pt',map_location=device,weights_only=False);model=Transition(kind).to(device);model.load_state_dict(ck['model']);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;ids=torch.tensor(rot['test'],device=device);result=evaluate(model,z,ids,mean,std,True)
 for split,split_ids in [('validation',torch.tensor(rot['validation'],device=device))]:
  buf=io.BytesIO();np.savez_compressed(buf,case_indices=split_ids.cpu().numpy(),times=times[split_ids].cpu().numpy(),normalized_rollout=predictions(model,z,split_ids,True).cpu().numpy(),mean=mean.cpu().numpy(),std=std.cpu().numpy(),physical_scales=scale.cpu().numpy());data=buf.getvalue();name=f'fold{k:02}-{split}-predictions.npz';(folder/name).write_bytes(data);upload(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
 buf=io.BytesIO();np.savez_compressed(buf,case_indices=ids.cpu().numpy(),times=times[ids].cpu().numpy(),normalized_rollout=predictions(model,z,ids,True).cpu().numpy(),mean=mean.cpu().numpy(),std=std.cpu().numpy(),physical_scales=scale.cpu().numpy());data=buf.getvalue();name=f'fold{k:02}-test-predictions.npz';(folder/name).write_bytes(data);upload(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
 base=Transition('control').to(device);base.set_normalization(mean,std);baseline=evaluate(base,z,ids,mean,std,True);test=dict(fold=k,rotation=rot['rotation'],kind=kind,training_fold_count=8,selected_epoch=ck['epoch'],metrics=result,persistence=baseline,horizons=horizon_metrics(model,z,ids,mean,std));save(f'fold{k:02}-test.json',test);tests.append(test)
save('report.json',dict(success=True,folds=reports,tests=tests,scope='Fresh history8 GRU64 shared64 SiLU dropout0.1 integral-loss gated model on frozen rotation0 train8/val1/test1 split. Four-state range-normalized integral selection; no test-driven tuning. Previously examined data.'))
save('manifest.json',manifest.copy());save('complete.json',dict(success=True,report_sha256=hashlib.sha256((folder/'report.json').read_bytes()).hexdigest(),folds=1))
