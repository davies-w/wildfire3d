"""GPU-only coordinate fit. Every training space-time sample once per epoch."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import torch,numpy as np,json,io,time,traceback,hashlib
from pathlib import Path
from coordinate_model import CoordinateMLP,physical
from original_cnn import encode
from runtime import upload
R=Path(__file__).parent

def main():
 assert torch.cuda.is_available(),'No laptop training';torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False
 plan=json.loads((R/'coverage-plan.json').read_text());c=json.loads((R/'cases.json').read_text())[0];name=c['case'];raw=np.load(R/'data/fields'/(name+'.npy'));times=np.load(R/'data/fields'/(name+'-time.npy'));n=len(times);cells=48*32*32;assert n==91
 sc=torch.tensor(json.loads((R/'scales.json').read_text())['encoded_std'],device='cuda');truth=torch.from_numpy(raw.transpose(0,2,3,4,1).reshape(n,cells,6).copy()).cuda();target=torch.from_numpy(encode(raw,c['wind_speed']).transpose(0,2,3,4,1).reshape(n,cells,6).copy()).cuda()
 grid=torch.stack(torch.meshgrid(*[(torch.arange(s,device='cuda')+.5)/s*2-1 for s in [48,32,32]],indexing='ij'),-1).reshape(cells,3);tt=torch.tensor(times/90-1,device='cuda',dtype=torch.float32)
 trainframes=torch.tensor(plan['train_frames'],device='cuda');trainids=(trainframes[:,None]*cells+torch.arange(cells,device='cuda')).flatten();batch=plan['batch_size'];epochs=plan['epochs'];stepsperepoch=(len(trainids)+batch-1)//batch
 def coords(ids):return torch.cat([grid[ids%cells],tt[ids//cells,None]],1)
 torch.manual_seed(plan['seed']);m=CoordinateMLP().cuda();opt=torch.optim.AdamW(m.parameters(),lr=.001,weight_decay=1e-5);sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=epochs*stepsperepoch,eta_min=1e-5);history=[];start_epoch=0;start_pos=0;step=0;aggregate=[0.,0];started=time.monotonic()
 def save(epoch,pos,label):
  state=dict(model=m.state_dict(),optimizer=opt.state_dict(),scheduler=sched.state_dict(),epoch=epoch,next_batch=pos,step=step,aggregate=aggregate,history=history,plan=plan,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all());b=io.BytesIO();torch.save(state,b);upload(label+'.pt',b.getvalue())
 resume=R/'data/resume/coordinate.pt'
 if resume.exists():
  s=torch.load(resume,map_location='cuda',weights_only=False);assert s['plan']==plan;m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer']);sched.load_state_dict(s['scheduler']);start_epoch=s['epoch'];start_pos=s['next_batch'];step=s['step'];aggregate=s['aggregate'];history=s['history'];torch.set_rng_state(s['cpu_rng'].cpu());torch.cuda.set_rng_state_all([x.cpu() for x in s['cuda_rng']])
 with torch.no_grad():p=m(coords(trainids[:32])).clone()
 b=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),scheduler=sched.state_dict()),b);b.seek(0);s=torch.load(b,map_location='cuda',weights_only=False);m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer']);sched.load_state_dict(s['scheduler'])
 with torch.no_grad():assert torch.equal(p,m(coords(trainids[:32])))
 upload('cuda-resume-check.json',json.dumps(dict(passed=True,parameters=sum(v.numel() for v in m.parameters()),training_samples_per_epoch=len(trainids),steps_per_epoch=stepsperepoch)).encode())
 def evaluate(epoch,trainloss=None,final=False):
  rows=[];projections={};m.eval()
  with torch.no_grad():
   for frame in range(n):
    sums=torch.zeros(6,device='cuda');phys=torch.zeros(6,device='cuda');hot=torch.zeros(3,device='cuda');burn=torch.zeros(2,device='cuda');q=torch.zeros(2,device='cuda');parts=[]
    for k in range(0,cells,batch):
     end=min(k+batch,cells);ids=torch.arange(frame*cells+k,frame*cells+end,device='cuda');p=m(coords(ids));y=target[frame,k:end];r=truth[frame,k:end];v=physical(p,c['wind_speed']);sums+=((p-y).abs()/sc).sum(0);phys+=(v-r).abs().sum(0);hm=r[:,0]>50;bm=r[:,1]>.01
     hot+=torch.stack([(v[:,0]-r[:,0]).abs()[hm].sum(),(r[:,0]-20).abs()[hm].sum(),hm.sum()]);burn+=torch.stack([(v[:,1]-r[:,1]).abs()[bm].sum(),bm.sum()]);q+=torch.stack([v[:,1].sum(),r[:,1].sum()])*.125
     if final and frame in plan['projection_frames']:parts.append(v.cpu().numpy())
    rows.append(dict(frame=frame,time_s=float(times[frame]),split='validation_time' if frame in plan['validation_frames'] else 'train',objective_MAE=float(sums.mean()/cells),channel_objective_MAE=(sums/cells).cpu().tolist(),channel_physical_MAE=(phys/cells).cpu().tolist(),hot_cells=int(hot[2]),burning_cells=int(burn[1]),hot_temperature_MAE_C=float(hot[0]/hot[2]) if hot[2]>0 else None,hot_temperature_relative_percent=float(100*hot[0]/hot[1]) if hot[1]>0 else None,burning_HRR_MAE_kWm3=float(burn[0]/burn[1]) if burn[1]>0 else None,predicted_HRR_kW=float(q[0]),truth_HRR_kW=float(q[1]),HRR_absolute_error_kW=float(abs(q[0]-q[1]))))
    if parts:
     v=np.concatenate(parts).reshape(48,32,32,6);r=raw[frame];projections[f'pred_{frame}']=v[:,:,:,[0,1]].max(1);projections[f'truth_{frame}']=r[[0,1]].max(2).transpose(1,2,0)
  m.train();rec=dict(epoch=epoch,step=step,learning_rate=opt.param_groups[0]['lr'],mean_training_loss=trainloss,rows=rows,elapsed_s=time.monotonic()-started);upload(f'epoch-{epoch:03}.json',json.dumps(rec).encode())
  if projections:b=io.BytesIO();np.savez_compressed(b,**projections);upload('projections.npz',b.getvalue())
  return rec
 if step==0:history.append(evaluate(0));save(0,0,'epoch-000')
 try:
  for epoch in range(start_epoch,epochs):
   gen=torch.Generator(device='cuda').manual_seed(plan['seed']+epoch);order=torch.randperm(len(trainids),device='cuda',generator=gen)
   for pos in range(start_pos if epoch==start_epoch else 0,stepsperepoch):
    ids=trainids[order[pos*batch:(pos+1)*batch]];p=m(coords(ids));y=target.flatten(0,1)[ids];loss=((p-y).abs()/sc).mean();assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();sched.step();step+=1;aggregate[0]+=float(loss.detach())*len(ids);aggregate[1]+=len(ids)
    if step%250==0:save(epoch,pos+1,f'step-{step:06}')
   assert aggregate[1]==len(trainids);history.append(evaluate(epoch+1,aggregate[0]/aggregate[1],final=epoch+1==epochs));aggregate=[0.,0];save(epoch+1,0,f'epoch-{epoch+1:03}');print('EPOCH',epoch+1,history[-1]['mean_training_loss'],flush=True)
 except BaseException:
  try:save(epoch,pos+1,'interrupted')
  except Exception:pass
  raise
 report=json.dumps(dict(plan=plan,history=history,elapsed_s=time.monotonic()-started)).encode();upload('report.json',report);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(report).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:upload('error.txt',traceback.format_exc().encode());raise
