"""Cloud-only minimal-state sequence learning; all tests gated behind ten selections."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from pathlib import Path
import json,io,time,hashlib,random
import numpy as np
import torch
from model import Transition,normalize_fit
from runtime import upload
R=Path(__file__).resolve().parent;P=json.loads((R/'coverage-plan.json').read_text());meta=json.loads((R/'schema.json').read_text());start=time.monotonic()
torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'
device='cuda';torch.manual_seed(3516);np.random.seed(3516);random.seed(3516)
a=np.load(R/'data/sequences.npz');raw=torch.tensor(a['state'],device=device);times=torch.tensor(a['time'],device=device);geom=torch.tensor(a['geometry'],device=device);config=torch.tensor(a['configuration'],device=device);scale=torch.tensor(meta['physical_encoding_scales'],device=device)
dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt
external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales'],device=device)
active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5)
assert external.shape==(520,90,9)
folder=R/'results';folder.mkdir(exist_ok=True);manifest={}
def save(name,obj):
 b=json.dumps(obj,allow_nan=False).encode();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def checkpoint(name,obj):
 f=io.BytesIO();torch.save(obj,f);b=f.getvalue();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def statehash(state):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in state.values())).hexdigest()
def mean_groups(value,ids):return torch.stack([value[config[ids]==c].mean(0) for c in torch.unique(config[ids])]).mean(0)
def objective(pred,target):return (pred-target).square().mean(-1)
def history_at(z,ids,js):return z[ids[:,None],(js[:,None]+torch.arange(-3,1,device=z.device)[None,:]).clamp_min(0)]
def advance(history,state):return torch.cat([history[:,1:],state[:,None]],1)
def phase_mae(errors,phase,ids):
 den=phase.sum(1);keep=den>0
 return mean_groups((errors*phase[:,:,None]).sum(1)[keep]/den[keep,None],ids[keep]).cpu().tolist() if bool(keep.any()) else None
@torch.no_grad()
def prefix_memory(model,z,ids,js):
 if model.kind=='mlp':return None
 memory=torch.zeros(len(ids),32,device=z.device);length=int(js.max())
 if length==0:return memory
 ii=ids[:,None].expand(-1,length).flatten();jj=torch.arange(length,device=z.device).expand(len(ids),-1).flatten()
 history=history_at(z,ii,jj);inputs=torch.cat([history.flatten(1),external[ii,jj]],-1).reshape(len(ids),length,21)
 output,_=model.cell(inputs);memory=output[torch.arange(len(ids),device=z.device),(js-1).clamp_min(0)]
 return torch.where((js>0)[:,None],memory,torch.zeros_like(memory))
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
@torch.no_grad()
def evaluate(model,z,ids,mean,std,details=False):
 model.eval();out={}
 for mode in ['one_step','rollout']:
  pred=predictions(model,z,ids,mode=='rollout');err=objective(pred,z[ids,1:]).mean(1);phys=torch.sinh(pred*std+mean)*scale
  finite=bool(torch.isfinite(phys).all() and torch.isfinite(err).all());entry=dict(objective=float(mean_groups(err,ids)) if finite else 1e30,finite=finite)
  if not finite:out[mode]=entry;continue
  errors=(phys-raw[ids,1:]).abs();mae=errors.mean(1);entry['physical_MAE_by_feature']=mean_groups(mae,ids).cpu().tolist()
  entry['physical_MAE_by_window']={name:phase_mae(errors,p,ids) for name,p in [('ignition',times[ids,1:]<=20),('post_source_to90',(times[ids,1:]>20)&(times[ids,1:]<=90)),('after90',times[ids,1:]>90),('active',active[ids]),('quiet',~active[ids])]}
  curve=torch.cat([raw[ids,0:1],phys],1);change=curve[:,1:,:2]-curve[:,:-1,:2]
  entry['minimum_by_feature']=phys.amin((0,1)).cpu().tolist();entry['negative_fraction_by_feature']=mean_groups((phys<0).float().mean(1),ids).cpu().tolist();entry['negative_magnitude_mean_by_feature']=mean_groups((-phys).clamp_min(0).mean(1),ids).cpu().tolist();entry['mass_increase_fraction']=mean_groups((change>1e-6).float().mean(1),ids).cpu().tolist();entry['mass_increase_total_kg']=mean_groups(change.clamp_min(0).sum(1),ids).cpu().tolist()
  integral=(.5*(curve[:,1:,2]+curve[:,:-1,2])*dt[ids]).sum(1);truthintegral=(.5*(raw[ids,1:,2]+raw[ids,:-1,2])*dt[ids]).sum(1)
  entry['released_fuel_integral_MAE_kg']=float(mean_groups((integral-truthintegral).abs(),ids))
  peak=curve[:,:,2].max(1);truthpeak=raw[ids,:,2].max(1);entry['peak_release_MAE_kg_s']=float(mean_groups((peak.values-truthpeak.values).abs(),ids));entry['peak_time_MAE_s']=float(mean_groups((times[ids,peak.indices]-times[ids,truthpeak.indices]).abs(),ids))
  if details:entry['cases']=[dict(case=meta['cases'][n]['case'],configuration=int(config[n]),objective=float(err[j]),physical_MAE_by_feature=mae[j].cpu().tolist(),released_fuel_integral_kg=float(integral[j]),truth_released_fuel_kg=float(truthintegral[j])) for j,n in enumerate(ids.tolist())]
  out[mode]=entry
 return out

def rngstate():return dict(torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all(),numpy=np.random.get_state(),python=random.getstate())
def restore_rng(x):torch.set_rng_state(x['torch'].cpu());torch.cuda.set_rng_state_all([state.cpu() for state in x['cuda']]);np.random.set_state(x['numpy']);random.setstate(x['python'])
checks=[]
for kind in P['arms']:
 m=Transition(kind).to(device)
 with torch.no_grad():
  (m.head if kind=='gru' else m.net[-1]).weight.fill_(.001)
 b=torch.zeros(4,4,3,device=device);u=external[:4,0];q=m(b,u);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition(kind).to(device);m2.load_state_dict(torch.load(buf,weights_only=False,map_location=device));assert torch.equal(q,m2(b,u));q.sum().backward();g=[p.grad.clone() for p in m.parameters()];m.zero_grad();m(b,u).sum().backward();assert all(torch.equal(v,p.grad) for v,p in zip(g,m.parameters()))
 m.zero_grad();history=b;memory=None;loss=0
 for j in range(32):
  state,memory=m.step(history,u,memory);loss+=state.square().mean()+state.sum();history=advance(history,state)
 loss.backward();assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in m.parameters())
 if kind=='gru':
  xx=torch.randn(4,12,21,device=device);whole,_=m.cell(xx);mem=None;seq=[]
  for j in range(12):
   yy,mem=m.cell(xx[:,j:j+1],mem);seq.append(yy)
  assert torch.allclose(torch.cat(seq,1),whole,atol=2e-6,rtol=2e-5),'CUDA prefix equivalence'
 checks.append(dict(kind=kind,parameters=sum(p.numel() for p in m.parameters()),exact_replay=True,backward32=True))
save('cuda-check.json',dict(passed=True,checks=checks))
# Exercise the actual saved checkpoint on the actual GPU before any fitting.
resume_probe=R/'data/resume/fold15.pt'
if resume_probe.exists():
 c=torch.load(resume_probe,map_location=device,weights_only=False);probe_model=Transition(c['kind']).to(device);probe_model.load_state_dict(c['model']);probe_opt=torch.optim.AdamW(probe_model.parameters(),lr=P['learning_rate'],weight_decay=1e-4);probe_opt.load_state_dict(c['optimizer'])
 restore_rng(c['rng']);cpu_draw=torch.rand(8);gpu_draw=torch.rand(8,device=device);np_draw=np.random.random(8);py_draw=random.random()
 restore_rng(c['rng']);assert torch.equal(cpu_draw,torch.rand(8));assert torch.equal(gpu_draw,torch.rand(8,device=device));assert np.array_equal(np_draw,np.random.random(8));assert py_draw==random.random();restore_rng(c['rng'])
 x=torch.zeros(4,4,3,device=device);u=external[:4,0];y=probe_model(x,u);buf=io.BytesIO();torch.save(probe_model.state_dict(),buf);buf.seek(0);probe_model2=Transition(c['kind']).to(device);probe_model2.load_state_dict(torch.load(buf,map_location=device,weights_only=False));assert torch.equal(y,probe_model2(x,u))
 save('resume-cloud-check.json',dict(passed=True,checkpoint_epoch=c['epoch'],cpu_rng_replay=True,cuda_rng_replay=True,numpy_rng_replay=True,python_rng_replay=True,optimizer_loaded=True,saved_model_forward_replay=True,optimization_performed=False))
 del probe_model,probe_model2,probe_opt,c
reports=[]
jobs=[(rot,kind) for rot in meta['rotations'] for kind in P['arms']]
for k,(rotation,kind) in enumerate(jobs):
 previous=R/'data/resume'/f'fold{k:02}-report.json'
 if previous.exists():
  old=json.loads(previous.read_text());assert old['fold']==k
  ck=torch.load(R/'data/resume'/f'fold{k:02}-selected.pt',map_location='cpu',weights_only=False);checkpoint(f'fold{k:02}-selected.pt',ck);save(f'fold{k:02}-report.json',old);reports.append(old);continue
 train=torch.tensor(rotation['train'],device=device);valid=torch.tensor(rotation['validation'],device=device)
 torch.manual_seed(3516);model=Transition(kind).to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=P['learning_rate'],weight_decay=1e-4);mean,std=normalize_fit(raw,train,config,scale);z=(torch.asinh(raw/scale)-mean)/std
 # Equal active/quiet contribution within each TRAIN history, then inverse replica count.
 weights=torch.zeros(520,90,device=device)
 for n in train.tolist():
  ac=active[n];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);replicas=int((config[train]==config[n]).sum())
  weights[n]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/replicas
 best=1e30;significant=1e30;stale=0;history=[];best_state=None;best_epoch=0;epoch=0;globalstep=0;resume_start=1;initial_hash=statehash(model.state_dict())
 resume=R/'data/resume'/f'fold{k:02}.pt'
 if resume.exists():
  ck=torch.load(resume,map_location=device,weights_only=False);assert ck['fold']==k and ck['schema_hash']==hashlib.sha256((R/'schema.json').read_bytes()).hexdigest();model.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer']);history=ck['history'];best=ck['best'];significant=ck['significant'];stale=ck['stale'];best_state=ck['best_state'];best_epoch=ck['best_epoch'];globalstep=ck['globalstep'];resume_start=ck['epoch']+1;restore_rng(ck['rng'])
 def pack():return dict(fold=k,rotation=rotation['rotation'],kind=kind,epoch=epoch,model=model.state_dict(),optimizer=optimizer.state_dict(),mean=mean,std=std,best=best,significant=significant,stale=stale,best_state=best_state,best_epoch=best_epoch,history=history,globalstep=globalstep,rng=rngstate(),schema_hash=hashlib.sha256((R/'schema.json').read_bytes()).hexdigest(),checkpoint_boundary='completed epoch; next epoch order deterministic')
 if not history:
  save(f'fold{k:02}-baseline.json',evaluate(model,z,valid,mean,std,True));history.append(dict(epoch=0,train=evaluate(model,z,train,mean,std),validation=evaluate(model,z,valid,mean,std)))
 stop='epoch_cap_not_convergence'
 for epoch in range(resume_start,P['epochs_max']+1):
  if time.monotonic()-start>P['budget']['soft_seconds']:
   epoch-=1;checkpoint(f'fold{k:02}-deadline.pt',pack());save('partial.json',dict(reason='soft_deadline',completed_folds=len(reports),active_fold=k,epoch=epoch));raise RuntimeError('Deadline checkpoint retained; no automatic continuation')
  h=next(x['steps'] for x in reversed(P['horizon_curriculum']) if epoch>=x['first_epoch']);windows=[(int(n),j) for n in train.tolist() for j in range(0,90,h)];order=np.random.default_rng(3516+rotation['rotation']*10000+epoch).permutation(len(windows));model.train();total=0.;batches=0
  for off in range(0,len(windows),P['batch_windows']):
   batch=[windows[i] for i in order[off:off+P['batch_windows']]];ids=torch.tensor([n for n,j in batch],device=device);js=torch.tensor([j for n,j in batch],device=device);hist=history_at(z,ids,js);memory=prefix_memory(model,z,ids,js);loss=0.;normal=0.
   for step in range(h):
    jj=(js+step).clamp_max(89);keep=js+step<90;state,memory=model.step(hist,external[ids,jj],memory);loss+=(objective(state,z[ids,jj+1])*weights[ids,jj]*keep).sum();normal+=keep.sum();hist=advance(hist,state)
   loss=loss/normal;assert bool(torch.isfinite(loss)),f'Nonfinite fold{k} epoch{epoch}';optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step();globalstep+=1;total+=float(loss);batches+=1
  tr=evaluate(model,z,train,mean,std);va=evaluate(model,z,valid,mean,std);score=va['rollout']['objective'];row=dict(epoch=epoch,horizon=h,training_window_objective=total/batches,train=tr,validation=va);history.append(row)
  if best_state is None or score<best:best=score;best_epoch=epoch;best_state={n:v.detach().cpu().clone() for n,v in model.state_dict().items()}
  if epoch in [21,41,61]:significant=score;stale=0
  elif score<significant-max(P['improvement_absolute'],P['improvement_relative']*abs(significant)):significant=score;stale=0
  elif epoch>61:stale+=1
  save(f'fold{k:02}-epoch{epoch:03}.json',row)
  checkpoint(f'fold{k:02}-epoch{epoch:03}.pt',pack())
  print('FOLD',k,'EPOCH',epoch,'TRAIN',tr['rollout']['objective'],'VAL',score,flush=True)
  if epoch>=P['minimum_epochs'] and stale>=P['patience_epochs']:stop='validation_patience';break
 assert best_state is not None
 checkpoint(f'fold{k:02}-final.pt',pack());final=dict(train=evaluate(model,z,train,mean,std,True),validation=evaluate(model,z,valid,mean,std,True));model.load_state_dict(best_state)
 checkpoint(f'fold{k:02}-selected.pt',dict(model=best_state,mean=mean.cpu(),std=std.cpu(),epoch=best_epoch,fold=k,rotation=rotation['rotation'],kind=kind))
 report=dict(fold=k,rotation=rotation['rotation'],kind=kind,initial_hash=initial_hash,epochs=epoch,selected_epoch=best_epoch,stop_reason=stop,history=history,final=final,selected=dict(train=evaluate(model,z,train,mean,std,True),validation=evaluate(model,z,valid,mean,std,True)))
 save(f'fold{k:02}-report.json',report);reports.append(report)
assert len(reports)==20
save('selection-freeze.json',dict(selected=[dict(fold=r['fold'],epoch=r['selected_epoch']) for r in reports],test_not_evaluated_yet=True))
@torch.no_grad()
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
  errors=torch.cat(parts).reshape(len(ids),91-h,3);hold_errors=torch.cat(hold).reshape(len(ids),91-h,3)
  finite=bool(torch.isfinite(errors).all())
  windows={'ignition':times[ids,h:]<=20,'post_source_to90':(times[ids,h:]>20)&(times[ids,h:]<=90),'after90':times[ids,h:]>90,'active':active[ids,h-1:],'quiet':~active[ids,h-1:]}
  result[str(h)]=dict(steps=h,nominal_seconds=2*h,finite=finite,model_MAE=aggregate(parts) if finite else None,no_change_MAE=aggregate(hold),mean_absolute_truth=aggregate(truths),model_windows={w:phase_mae(errors,m,ids) if finite else None for w,m in windows.items()},no_change_windows={w:phase_mae(hold_errors,m,ids) for w,m in windows.items()},scope='All valid forecast origins; observed history through origin, predictions thereafter; windows by endpoint')
 return result
tests=[]
for k,(rot,kind) in enumerate(jobs):
 ck=torch.load(folder/f'fold{k:02}-selected.pt',map_location=device,weights_only=False);model=Transition(kind).to(device);model.load_state_dict(ck['model']);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;ids=torch.tensor(rot['test'],device=device);result=evaluate(model,z,ids,mean,std,True)
 buf=io.BytesIO();np.savez_compressed(buf,case_indices=ids.cpu().numpy(),times=times[ids].cpu().numpy(),normalized_rollout=predictions(model,z,ids,True).cpu().numpy(),mean=mean.cpu().numpy(),std=std.cpu().numpy(),physical_scales=scale.cpu().numpy());data=buf.getvalue();name=f'fold{k:02}-test-predictions.npz';(folder/name).write_bytes(data);upload(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
 baseline=evaluate(Transition().to(device),z,ids,mean,std,True);test=dict(fold=k,rotation=rot['rotation'],kind=kind,selected_epoch=ck['epoch'],metrics=result,persistence=baseline,horizons=horizon_metrics(model,z,ids,mean,std));save(f'fold{k:02}-test.json',test);tests.append(test)
save('report.json',dict(success=True,folds=reports,tests=tests,scope='Water/dryfuel/fuel-gas release only; char inert; no gas combustion or heat prediction; reshuffled data not historically pristine'))
save('manifest.json',manifest.copy());save('complete.json',dict(success=True,report_sha256=hashlib.sha256((folder/'report.json').read_bytes()).hexdigest(),folds=20))
