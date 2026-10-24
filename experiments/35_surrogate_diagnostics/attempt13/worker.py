"""Cloud-only 10-fold sequence learning with validation selection and delayed test evaluation."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from pathlib import Path
import json,io,time,hashlib,random,copy,traceback
import numpy as np
import torch
from model import Transition,normalize_fit
from runtime import upload
R=Path(__file__).resolve().parent
P=json.loads((R/'coverage-plan.json').read_text());meta=json.loads((R/'schema.json').read_text());start=time.monotonic()
torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
assert torch.cuda.is_available(),'Cloud CUDA required; no local training'
device='cuda';torch.manual_seed(3513);np.random.seed(3513);random.seed(3513)
a=np.load(R/'data/sequences.npz');raw=torch.tensor(a['state'],device=device);mask=torch.tensor(a['mask'],device=device);times=torch.tensor(a['time'],device=device);geom=torch.tensor(a['geometry'],device=device);config=torch.tensor(a['configuration'],device=device);scale=torch.tensor(meta['physical_encoding_scales'],device=device)
dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt
external=torch.cat([geom[:,None,:].expand(-1,90,-1),torch.full_like(dt[:,:,None],.2),on[:,:,None],dt[:,:,None]/2],-1)
assert external.shape==(520,90,13)
folder=R/'results';folder.mkdir(exist_ok=True);manifest={}
def save(name,obj):
 b=json.dumps(obj,allow_nan=False).encode();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def checkpoint(name,obj):
 f=io.BytesIO();torch.save(obj,f);b=f.getvalue();(folder/name).write_bytes(b);upload(name,b);manifest[name]=hashlib.sha256(b).hexdigest()
def statehash(state):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in state.values())).hexdigest()
def mean_groups(value,ids):
 return torch.stack([value[config[ids]==c].mean(0) for c in torch.unique(config[ids])]).mean(0)
def objective(pred,target,m):return ((pred-target).square()*m).sum(-1)/m.sum(-1).clamp_min(1)
def feedback(state,mean,std):
 result=state.clone()
 for j,(pi,ix) in enumerate(zip(meta['presence_indices'],meta['shape_indices'])):
  active=torch.sinh(state[:,pi]*std[pi]+mean[pi])>.5
  indices=ix+(meta['velocity_indices'] if j==0 else [])
  result[:,indices]=torch.where(active[:,None],state[:,indices],torch.zeros_like(state[:,indices]))
 return result
@torch.no_grad()
def predictions(model,z,ids,rollout,mean,std):
 if not rollout:return model(z[ids,:-1].reshape(-1,52),external[ids].reshape(-1,13)).reshape(len(ids),90,52)
 current=z[ids,0];out=[]
 for j in range(90):
  predicted=model(current,external[ids,j]);out.append(predicted);current=feedback(predicted,mean,std)
 return torch.stack(out,1)
@torch.no_grad()
def evaluate(model,z,ids,mean,std,details=False):
 model.eval();out={}
 for mode in ['one_step','rollout']:
  pred=predictions(model,z,ids,mode=='rollout',mean,std);m=mask[ids,1:];err=objective(pred,z[ids,1:],m).mean(1)
  finite=bool(torch.isfinite(pred).all() and torch.isfinite(err).all());score=float(mean_groups(err,ids)) if finite else 1e30
  entry=dict(objective=score,finite=finite)
  if True:
   phys=torch.sinh(pred*std+mean)*scale;target=raw[ids,1:];finitephys=torch.isfinite(phys);safe=torch.where(finitephys,phys,torch.zeros_like(phys));den=m.sum(1).clamp_min(1)
   mae=((safe-target).abs()*m).sum(1)/den;entry['physical_MAE_by_feature']=mean_groups(mae,ids).cpu().tolist() if bool(finitephys.all()) else None
   curve=torch.cat([raw[ids,0:1,0],safe[:,:,0]],1);truthcurve=raw[ids,:,0];energy=(.5*(curve[:,1:]+curve[:,:-1])*(times[ids,1:]-times[ids,:-1])).sum(1);truthenergy=(.5*(truthcurve[:,1:]+truthcurve[:,:-1])*(times[ids,1:]-times[ids,:-1])).sum(1);entry['gas_released_energy_MAE_kJ']=float(mean_groups((energy-truthenergy).abs(),ids)) if bool(finitephys.all()) else None
   pi=meta['presence_indices'][0];hot=safe[:,:,pi]>.5;truehot=target[:,:,pi]>.5;tp=(hot&truehot).sum(1).float();fp=(hot&~truehot).sum(1).float();fn=(~hot&truehot).sum(1).float();counts=mean_groups(torch.stack([tp,fp,fn],1),ids).cpu().tolist();tp,fp,fn=counts;entry['hot_presence']=dict(precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,F1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,counts_configuration_mean=counts)
   entry['nonfinite_physical_cells']=int((~finitephys).sum());entry['negative_gas_HRR_fraction']=float((safe[:,:,0]<0).float().mean());entry['negative_material_mass_fraction']=float((safe[:,:,[9,14,19,24]]<0).float().mean())
   entry['physical_MAE_by_window']={}
   for window,tw in [('ignition',times[ids,1:]<=20),('post_source_to90',(times[ids,1:]>20)&(times[ids,1:]<=90)),('after90',times[ids,1:]>90)]:
    wm=m*tw[:,:,None];we=((safe-target).abs()*wm).sum(1)/wm.sum(1).clamp_min(1);entry['physical_MAE_by_window'][window]=mean_groups(we,ids).cpu().tolist() if bool(finitephys.all()) else None
  if details:
   entry['cases']=[]
   for j,n in enumerate(ids.tolist()):
    entry['cases'].append(dict(case=meta['cases'][n]['case'],configuration=int(config[n]),source=meta['cases'][n]['source'],objective=float(err[j]) if bool(torch.isfinite(err[j])) else None,physical_MAE_by_feature=mae[j].cpu().tolist() if bool(finitephys[j].all()) else None))
   # Covariance validity is diagnostic; prediction is never silently projected to PSD.
   bad=total=0
   for pi,ix in zip(meta['presence_indices'],meta['shape_indices']):
    active=safe[:,:,pi]>.5;v=safe[:,:,ix[3:]];cov=torch.stack([v[:,:,0],v[:,:,3],v[:,:,4],v[:,:,3],v[:,:,1],v[:,:,5],v[:,:,4],v[:,:,5],v[:,:,2]],-1).reshape(-1,3,3);act=active.flatten()
    if bool(act.any()):bad+=int((torch.linalg.eigvalsh(cov[act].double())[:,0]<-1e-6).sum());total+=int(act.sum())
   entry['invalid_active_covariance_fraction']=bad/total if total else None
  out[mode]=entry
 return out

def rngstate():return dict(torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all(),numpy=np.random.get_state(),python=random.getstate())
def restore_rng(x):torch.set_rng_state(x['torch'].cpu());torch.cuda.set_rng_state_all(x['cuda']);np.random.set_state(x['numpy']);random.setstate(x['python'])
# CUDA serialization and gradient replay, no optimization before check.
m=Transition().to(device);b=torch.zeros(4,52,device=device);u=external[:4,0];q=m(b,u);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition().to(device);m2.load_state_dict(torch.load(buf,weights_only=False,map_location=device));assert torch.equal(q,m2(b,u));q.sum().backward();g=[p.grad.clone() for p in m.parameters()];m.zero_grad();m(b,u).sum().backward();assert all(torch.equal(v,p.grad) for v,p in zip(g,m.parameters()))
m.zero_grad();current=b;loss=0
for j in range(8):
 predicted=m(current,u);loss=loss+predicted.sum();current=feedback(predicted,torch.zeros(52,device=device),torch.ones(52,device=device))
loss.backward();assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in m.parameters())
save('cuda-check.json',dict(passed=True,exact_forward_replay=True,exact_gradient_replay=True,eight_step_backward=True,input_shape=[4,65],output_shape=[4,52]))
reports=[]
for rotation in meta['rotations']:
 k=rotation['rotation'];previous=R/'data/resume'/f'fold{k:02}-report.json'
 if previous.exists():
  old=json.loads(previous.read_text());assert old['fold']==k
  ck=torch.load(R/'data/resume'/f'fold{k:02}-selected.pt',map_location='cpu',weights_only=False);checkpoint(f'fold{k:02}-selected.pt',ck);save(f'fold{k:02}-report.json',old);reports.append(old);continue
 train=torch.tensor(rotation['train'],device=device);valid=torch.tensor(rotation['validation'],device=device)
 torch.manual_seed(3513);model=Transition().to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=P['learning_rate'],weight_decay=1e-4);mean,std=normalize_fit(raw,mask,train,config,scale);z=(torch.asinh(raw/scale)-mean)/std;z=torch.where(mask.bool(),z,torch.zeros_like(z))
 best=1e30;significant=1e30;stale=0;history=[];best_state=None;best_epoch=0;epoch=0;globalstep=0;resume_start=1;initial_hash=statehash(model.state_dict())
 resume=R/'data/resume'/f'fold{k:02}.pt'
 if resume.exists():
  ck=torch.load(resume,map_location=device,weights_only=False);assert ck['fold']==k and ck['schema_hash']==hashlib.sha256((R/'schema.json').read_bytes()).hexdigest();model.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer']);history=ck['history'];best=ck['best'];significant=ck['significant'];stale=ck['stale'];best_state=ck['best_state'];best_epoch=ck['best_epoch'];globalstep=ck['globalstep'];resume_start=ck['epoch']+1;restore_rng(ck['rng'])
 def pack():return dict(fold=k,epoch=epoch,model=model.state_dict(),optimizer=optimizer.state_dict(),mean=mean,std=std,best=best,significant=significant,stale=stale,best_state=best_state,best_epoch=best_epoch,history=history,globalstep=globalstep,rng=rngstate(),schema_hash=hashlib.sha256((R/'schema.json').read_bytes()).hexdigest(),checkpoint_boundary='completed epoch; all windows covered; next epoch schedule deterministic')
 if not history:
  base=evaluate(model,z,valid,mean,std,True);save(f'fold{k:02}-baseline.json',base);row=dict(epoch=0,train=evaluate(model,z,train,mean,std),validation=evaluate(model,z,valid,mean,std));history.append(row)
 stop='epoch_cap_not_convergence'
 for epoch in range(resume_start,P['epochs_max']+1):
  if time.monotonic()-start>9900:epoch-=1;checkpoint(f'fold{k:02}-deadline.pt',pack());save('partial.json',dict(reason='soft_deadline',completed_folds=len(reports),active_fold=k,epoch=epoch));raise RuntimeError('Soft deadline; preserved epoch checkpoint, separately reserved continuation required')
  h=1 if epoch<=P['warmup_epochs'] else P['sequence_horizon_steps'];windows=[(int(n),j) for n in train.tolist() for j in range(0,90,h)];order=np.random.default_rng(3513+k*10000+epoch).permutation(len(windows));model.train();total=0.;batches=0
  counts={int(c):int((config[train]==c).sum()) for c in torch.unique(config[train])}
  for off in range(0,len(windows),P['batch_windows']):
   batch=[windows[i] for i in order[off:off+P['batch_windows']]];ids=torch.tensor([n for n,j in batch],device=device);js=torch.tensor([j for n,j in batch],device=device);state=z[ids,js];weight=torch.tensor([1/counts[int(config[n])] for n,j in batch],device=device);loss=0.;normal=0.
   for step in range(h):
    jj=(js+step).clamp_max(89);active=js+step<90;new=model(state,external[ids,jj]);state=torch.where(active[:,None],new,state);loss=loss+(objective(state,z[ids,jj+1],mask[ids,jj+1])*weight*active).sum();normal=normal+(weight*active).sum();state=feedback(state,mean,std)
   loss=loss/normal;assert bool(torch.isfinite(loss)),f'Nonfinite loss fold{k} epoch{epoch}';optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step();globalstep+=1;total+=float(loss);batches+=1
  tr=evaluate(model,z,train,mean,std);va=evaluate(model,z,valid,mean,std);score=va['rollout']['objective'];row=dict(epoch=epoch,horizon=h,training_window_objective=total/batches,train=tr,validation=va);history.append(row)
  # Select across every trained epoch; patience is reset when sequence training begins.
  if best_state is None or score<best:best=score;best_epoch=epoch;best_state={n:v.detach().cpu().clone() for n,v in model.state_dict().items()}
  if epoch==P['warmup_epochs']+1:significant=score;stale=0
  elif score<significant-max(P['improvement_absolute'],P['improvement_relative']*abs(significant)):significant=score;stale=0
  elif epoch>P['warmup_epochs']:stale+=1
  save(f'fold{k:02}-epoch{epoch:03}.json',row)
  if epoch%5==0:checkpoint(f'fold{k:02}-epoch{epoch:03}.pt',pack())
  print('FOLD',k,'EPOCH',epoch,'TRAIN',tr['rollout']['objective'],'VAL',score,flush=True)
  if epoch>=P['minimum_epochs'] and stale>=P['patience_epochs']:stop='validation_patience';break
 assert best_state is not None
 checkpoint(f'fold{k:02}-final.pt',pack());final=dict(train=evaluate(model,z,train,mean,std,True),validation=evaluate(model,z,valid,mean,std,True));model.load_state_dict(best_state)
 selected=dict(model=best_state,mean=mean.cpu(),std=std.cpu(),epoch=best_epoch,fold=k);checkpoint(f'fold{k:02}-selected.pt',selected)
 report=dict(fold=k,initial_hash=initial_hash,epochs=epoch,selected_epoch=best_epoch,stop_reason=stop,history=history,final=final,selected=dict(train=evaluate(model,z,train,mean,std,True),validation=evaluate(model,z,valid,mean,std,True)))
 save(f'fold{k:02}-report.json',report);reports.append(report)
# Test gate: no test metrics have been computed before all ten selected models exist.
assert len(reports)==10
save('selection-freeze.json',dict(selected=[dict(fold=r['fold'],epoch=r['selected_epoch']) for r in reports],test_not_evaluated_yet=True))
tests=[]
for rot in meta['rotations']:
 k=rot['rotation'];ck=torch.load(folder/f'fold{k:02}-selected.pt',map_location=device,weights_only=False);model=Transition().to(device);model.load_state_dict(ck['model']);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;z=torch.where(mask.bool(),z,torch.zeros_like(z));ids=torch.tensor(rot['test'],device=device);result=evaluate(model,z,ids,mean,std,True)
 buf=io.BytesIO();np.savez_compressed(buf,case_indices=ids.cpu().numpy(),times=times[ids].cpu().numpy(),normalized_rollout=predictions(model,z,ids,True,mean,std).cpu().numpy(),mean=mean.cpu().numpy(),std=std.cpu().numpy(),physical_scales=scale.cpu().numpy());data=buf.getvalue();name=f'fold{k:02}-test-predictions.npz';(folder/name).write_bytes(data);upload(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
 persistence=Transition().to(device);baseline=evaluate(persistence,z,ids,mean,std,True);test=dict(fold=k,selected_epoch=ck['epoch'],metrics=result,persistence=baseline);save(f'fold{k:02}-test.json',test);tests.append(test)
report=dict(success=True,folds=reports,tests=tests,scope='Full dataset; grouped new cross-validation, not historically pristine; compact-state predictions, not physical validation')
save('report.json',report);save('manifest.json',manifest.copy());save('complete.json',dict(success=True,report_sha256=hashlib.sha256((folder/'report.json').read_bytes()).hexdigest(),folds=10))
