"""Ten independent time-slice classifiers. Cloud GPU only; full evaluation each epoch."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import torch,numpy as np,json,io,time,hashlib,traceback,signal
from pathlib import Path
from model import HotUNet,metrics
from runtime import upload
R=Path(__file__).parent

def main():
 assert torch.cuda.is_available(),'GPU cloud only; no laptop optimization';torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False
 plan=json.loads((R/'coverage-plan.json').read_text());cases=json.loads((R/'cases.json').read_text());pop=json.loads((R/'data/class-population.json').read_text());frames=plan['selected_frames'];batch=plan['batch_size'];cells=48*32*32
 train=[i for i,c in enumerate(cases) if c['split']=='train'];val=[i for i,c in enumerate(cases) if c['split']=='validation'];assert len(train)==360 and len(val)==40
 coords=np.stack(np.meshgrid(*[(np.arange(n)+.5)/n*2-1 for n in [48,32,32]],indexing='ij')).astype(np.float32)
 geoms=np.load(R/'data/geometries.npz');density_scale=max(float(geoms[cases[i]['case']].max()) for i in train);assert density_scale>0
 static=[];packed=[];actual=[]
 for c in cases:
  a=np.radians(c['angle_deg']);conditions=np.array([c['wind_speed']/5,c['moisture']/.3,c['loading_multiplier']/1.3,c['crown_height_m']/10,np.cos(a),np.sin(a)],np.float32)
  static.append(np.concatenate([geoms[c['case']]/density_scale,coords,np.broadcast_to(conditions[:,None,None,None],(6,48,32,32))]))
  z=np.load(R/'data/labels'/(c['case']+'.npz'));packed.append(np.unpackbits(z['packed'][frames],axis=1,count=cells).reshape(len(frames),48,32,32));actual.append(z['time'][frames].tolist())
 x=torch.from_numpy(np.stack(static)).cuda();targets=torch.from_numpy(np.stack(packed)).cuda();del static,packed
 started=time.monotonic();stop_requested=False
 def handler(*args):
  nonlocal stop_requested;stop_requested=True
 signal.signal(signal.SIGTERM,handler)
 def sendjson(n,v):upload(n,json.dumps(v,allow_nan=False).encode())
 def balanced(z,y,positive):
  # Fixed TRAIN populations, not minibatch class counts. Cold-only at no-positive times.
  l=torch.nn.functional.binary_cross_entropy_with_logits(z,y,reduction='none');fraction=positive/(360*cells)
  if positive==0:return l.mean()
  return (.5*(l*y).mean()/fraction+.5*(l*(1-y)).mean()/(1-fraction))
 def digest(m):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
 reports=[]
 for ti,frame in enumerate(frames):
  previous=R/'data/resume'/f'time-{frame:03}-report.json'
  if previous.exists():
   done=json.loads(previous.read_text());assert done['frame']==frame;reports.append(done);continue
  torch.manual_seed(plan['seed']);m=HotUNet().cuda();opt=torch.optim.AdamW(m.parameters(),lr=plan['learning_rate'],weight_decay=plan['weight_decay']);positive=pop['positive'][frame];history=[];step=0;start_epoch=0;start_pos=0;aggregate=[0.,0];plateau_checks=0;initial_hash=digest(m);model_started=time.monotonic()
  resume=R/'data/resume'/f'time-{frame:03}.pt'
  if resume.exists():
   s=torch.load(resume,map_location='cuda',weights_only=False);assert s['plan']==plan and s['frame']==frame;m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer']);start_epoch=s['epoch'];start_pos=s['next_batch'];aggregate=s['aggregate'];history=s['history'];step=s['step'];plateau_checks=s['plateau_checks'];torch.set_rng_state(s['cpu_rng'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in s['cuda_rng']])
  def checkpoint(epoch,pos,label):
   b=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),epoch=epoch,next_batch=pos,aggregate=aggregate,history=history,step=step,plateau_checks=plateau_checks,plan=plan,frame=frame,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),b);upload(f'time-{frame:03}-{label}.pt',b.getvalue())
  def evaluate(epoch,loss=None):
   m.eval();rows=[]
   with torch.no_grad():
    for k in range(0,len(cases),batch):
     ids=list(range(k,min(k+batch,len(cases))));z=m(x[ids]);y=targets[ids,ti].float();pred=z>=0;bce=torch.nn.functional.binary_cross_entropy_with_logits(z,y,reduction='none');axes=(1,2,3)
     vals=torch.stack([(pred*(y>0)).sum(axes),(pred*(y==0)).sum(axes),((~pred)*(y>0)).sum(axes),((~pred)*(y==0)).sum(axes),(bce*y).sum(axes),(bce*(1-y)).sum(axes)],1).cpu().numpy();rows.extend(vals.tolist())
   summary={}
   for split,ids in [('train',train),('validation',val)]:
    configs=sorted({cases[i]['configuration'] for i in ids});grouped=np.array([np.mean([rows[i] for i in ids if cases[i]['configuration']==c],axis=0) for c in configs]);v=grouped.sum(0);res=metrics(v);fraction=positive/(360*cells)
    res['balanced_BCE']=float((.5*v[4]/fraction+.5*v[5]/(1-fraction))/(len(configs)*cells)) if positive else float((v[4]+v[5])/(len(configs)*cells))
    res['unweighted_BCE']=float((v[4]+v[5])/(len(configs)*cells));res['configurations']=len(configs)
    cms=[metrics(row) for row in grouped]
    for key in ['precision','recall','f1','iou']:
     vv=[cm[key] for cm in cms if cm[key] is not None];res['macro_'+key]=float(np.mean(vv)) if vv else None
    summary[split]=res
   rec=dict(frame=frame,nominal_time_s=frame*2,epoch=epoch,updates=step,learning_rate=opt.param_groups[0]['lr'],training_minibatch_loss=loss,summary=summary,elapsed_model_s=time.monotonic()-model_started)
   sendjson(f'time-{frame:03}-epoch-{epoch:03}.json',rec);b=io.BytesIO();np.savez_compressed(b,counts=np.array(rows),case=np.array([c['case'] for c in cases]),time=np.array(actual)[:,ti]);upload(f'time-{frame:03}-epoch-{epoch:03}-counts.npz',b.getvalue());m.train();return rec
  # Serialization replay on CUDA, with populated Adam moments, then reset exact original state.
  if step==0:
   original=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict()),original)
   bt=time.monotonic();ids=train[:batch];z=m(x[ids]);loss=balanced(z,targets[ids,ti].float(),positive);opt.zero_grad();loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters());opt.step();torch.cuda.synchronize();duration=time.monotonic()-bt
   with torch.no_grad():before=m(x[ids]).clone()
   replay=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict()),replay);replay.seek(0);s=torch.load(replay,map_location='cuda',weights_only=False);m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer'])
   with torch.no_grad():assert torch.equal(before,m(x[ids]))
   original.seek(0);s=torch.load(original,map_location='cuda',weights_only=False);m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer']);assert digest(m)==initial_hash
   sendjson(f'time-{frame:03}-cuda-check.json',dict(passed=True,initial_model_sha256=initial_hash,parameters=sum(p.numel() for p in m.parameters()),one_update_seconds=duration,train_positive_cells=positive,density_scale=density_scale));history.append(evaluate(0));checkpoint(0,0,'epoch-000')
  reason='maximum_epochs_not_plateau'
  try:
   for epoch in range(start_epoch,plan['maximum_epochs']):
    order=np.random.default_rng(plan['seed']+epoch).permutation(train);steps=(len(order)+batch-1)//batch
    for pos in range(start_pos if epoch==start_epoch else 0,steps):
     ids=order[pos*batch:(pos+1)*batch].tolist();y=targets[ids,ti].float();loss=balanced(m(x[ids]),y,positive);assert torch.isfinite(loss);opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();step+=1;aggregate[0]+=float(loss.detach())*len(ids);aggregate[1]+=len(ids)
     if step%500==0:checkpoint(epoch,pos+1,f'step-{step:06}')
     if stop_requested or time.monotonic()-started>plan['soft_deadline_s']:
      checkpoint(epoch,pos+1,'deadline');sendjson('partial.json',dict(success=False,reason='time_budget_not_convergence',frame=frame,epoch=epoch,next_batch=pos+1,completed_models=reports));return
    assert aggregate[1]==360
    history.append(evaluate(epoch+1,aggregate[0]/aggregate[1]));aggregate=[0.,0]
    # Compare two disjoint 10-epoch averages, both TRAIN and VAL; three consecutive checks.
    if epoch+1>=plan['minimum_epochs'] and (epoch+1)%10==0:
     stable=True;deltas={}
     for split in ['train','validation']:
      for key in ['balanced_BCE','precision','recall','f1']:
       old=[v['summary'][split][key] for v in history[-20:-10]];new=[v['summary'][split][key] for v in history[-10:]]
       if all(v is None for v in old+new):continue
       if any(v is None for v in old+new):stable=False;continue
       a,bv=float(np.mean(old)),float(np.mean(new));d=abs(bv-a);tol=max(.0001,.01*abs(a)) if key=='balanced_BCE' else .01;stable &= d<=tol;deltas[split+'/'+key]=dict(before=a,after=bv,absolute_change=d,tolerance=tol)
     plateau_checks=plateau_checks+1 if stable else 0;sendjson(f'time-{frame:03}-plateau-{epoch+1:03}.json',dict(stable=bool(stable),consecutive_checks=plateau_checks,deltas=deltas))
    checkpoint(epoch+1,0,f'epoch-{epoch+1:03}');print('EPOCH',frame*2,epoch+1,history[-1]['summary']['validation'],flush=True)
    if plateau_checks>=3:reason='prespecified_empirical_plateau';break
  except BaseException:
   try:checkpoint(epoch,pos+1,'interrupted')
   except Exception:pass
   raise
  result=dict(frame=frame,nominal_time_s=frame*2,reason=reason,epochs=history[-1]['epoch'],initial_model_sha256=initial_hash,final=history[-1],history=history);sendjson(f'time-{frame:03}-report.json',result);reports.append(result);del m,opt
 report=json.dumps(dict(plan=plan,models=reports,elapsed_s=time.monotonic()-started)).encode();upload('report.json',report);sendjson('complete.json',dict(success=True,report_sha256=hashlib.sha256(report).hexdigest()))
if __name__=='__main__':
 try:main()
 except BaseException:upload('error.txt',traceback.format_exc().encode());raise
