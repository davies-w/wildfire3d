"""Fresh-fit, oracle-source and source-only diagnostics; GPU-only training."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import json,time,io,copy,hashlib,traceback,math
import numpy as np
import torch
from torch import nn
from runtime import R,upload,inputs
from original_cnn import encode,load
from geometry_model import GeometryCNN
from diagnostic_model import OracleCNN
from snapshot_evaluation import metrics

def physical(p,wind):
 return torch.cat([20+100*torch.sinh(p[:,0:1].clamp(-5,5)),10*torch.expm1(p[:,1:2].clamp(0,10)),5*p[:,2:3]+wind,5*p[:,3:5],2*torch.expm1(p[:,5:6].clamp(0,10))],1)
def digest(m):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
def main():
 assert torch.cuda.is_available(),'No laptop training';torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
 from deterministic_interpolation import double_trilinear
 x=torch.randn(1,2,6,4,4,device='cuda');v=torch.randn(1,2,12,8,8,device='cuda');gs=[]
 for _ in range(2):
  z=x.clone().requires_grad_();o=double_trilinear(z);assert torch.allclose(o,torch.nn.functional.interpolate(z,scale_factor=2,mode='trilinear',align_corners=False),atol=2e-6,rtol=2e-5);gs.append(torch.autograd.grad(o,z,v)[0])
 assert torch.equal(*gs);upload('cuda-check.json',json.dumps({'passed':True}).encode())
 plan=json.loads((R/'coverage-plan.json').read_text());cs=json.loads((R/'cases.json').read_text());train=[c for c in cs if c['split']=='train'];geoms=dict(np.load(R/'data/geometries.npz'));arrays={c['case']:load(c) for c in cs};started=time.monotonic()
 assert len(train)==8 and all(c['split'] in ['train','validation'] for c in cs)
 sums=np.zeros(6);squares=np.zeros(6);count=0;qs={};X={}
 for c in cs:
  a,t=arrays[c['case']];qs[c['case']]=np.maximum(a[:,1],0).sum((1,2,3))*.125;X[c['case']]=inputs(c,t,geoms[c['case']])
  if c['split']=='train':
   for k in range(0,len(t),3):
    e=encode(a[k:k+3],c['wind_speed']).astype(np.float64);sums+=e.sum((0,2,3,4));squares+=(e*e).sum((0,2,3,4));count+=e.shape[0]*48*32*32
 scales=np.maximum(np.sqrt(np.maximum(squares/count-(sums/count)**2,0)),.05).astype('float32');sc=torch.tensor(scales,device='cuda')[None,:,None,None,None]
 qscale=max(float(np.concatenate([qs[c['case']] for c in train]).mean()),1.);logscale=max(float(np.log1p(np.concatenate([qs[c['case']] for c in train])).std()),1.)
 upload('scales.json',json.dumps(dict(encoded_std=scales.tolist(),physical_HRR_scale_kW=qscale,oracle_log_HRR_scale=logscale,computed_from='eight training configurations only')).encode())
 pairs=[]
 for cfg in sorted({c['configuration'] for c in cs if c['split']=='validation'}):
  cc=sorted([c for c in cs if c['configuration']==cfg],key=lambda c:c['replica'])
  if len(cc)>1:
   a,t=arrays[cc[0]['case']];b,tb=arrays[cc[1]['case']];assert np.array_equal(t,tb);pairs.append(dict(configuration=cfg,cases=[c['case'] for c in cc],metrics=metrics(np.array(a),np.array(b),t)))
 upload('seed-variability.json',json.dumps(dict(pairs=pairs,scope='Pairwise FDS realization differences; descriptive, not a calibrated irreducible error bound.')).encode())
 torch.manual_seed(3501);base=GeometryCNN().cuda();base_state=copy.deepcopy(base.state_dict());del base
 report=dict(scope=plan,curves={},initial_hashes={},scales=scales.tolist(),seed_pair_count=len(pairs));active=None
 def make(arm):
  torch.manual_seed(3501)
  if arm=='source':return nn.Sequential(nn.Linear(13,96),nn.SiLU(),nn.Linear(96,96),nn.SiLU(),nn.Linear(96,1),nn.Softplus()).cuda()
  if arm=='oracle':return OracleCNN(base_state).cuda()
  m=GeometryCNN().cuda();m.load_state_dict(base_state)
  return m
 def forward(m,arm,c,k,end):
  z=X[c['case']][k:end]
  if arm=='oracle':z=torch.cat([z,torch.tensor(np.log1p(qs[c['case']][k:end])/logscale,device='cuda')[:,None]],1)
  return m(z)
 def evaluate(m,arm,pool):
  rows=[];m.eval()
  with torch.no_grad():
   for c in pool:
    a,t=arrays[c['case']];n=len(t)
    if arm=='source':
     pred=forward(m,arm,c,0,n).flatten().cpu().numpy()*qscale;truth=qs[c['case']];rows.append(dict(case=c['case'],configuration=c['configuration'],split=c['split'],normalized_MAE=float(abs(pred-truth).mean()/qscale),HRR_MAE_kW=float(abs(pred-truth).mean()),truth_mean_HRR_kW=float(truth.mean()),predicted_mean_HRR_kW=float(pred.mean()),HRR_relative_L1_percent=float(100*abs(pred-truth).sum()/max(truth.sum(),1e-8))));continue
    err=torch.zeros(6,device='cuda');windows={w:dict(abs=torch.zeros(6,device='cuda'),den=torch.zeros(6,device='cuda'),hot=torch.zeros(3,device='cuda'),cells=0,qerr=torch.zeros((),device='cuda'),qden=torch.zeros((),device='cuda'),pdose=torch.zeros((48,32,32),device='cuda'),tdose=torch.zeros((48,32,32),device='cuda')) for w in ['all','post_source','late']};ambient=torch.tensor(np.array(a[0,5]),device='cuda')
    for k in range(0,n,3):
     end=min(k+3,n);p=forward(m,arm,c,k,end);raw=torch.tensor(np.array(a[k:end]),device='cuda');y=torch.tensor(encode(a[k:end],c['wind_speed']),device='cuda');err+=((p-y).abs()/sc).mean((2,3,4)).sum(0);b=physical(p,c['wind_speed'])
     for w,sel in [('all',t[k:end]>=0),('post_source',t[k:end]>=22),('late',t[k:end]>=120)]:
      if not sel.any():continue
      yy=raw[sel];bb=b[sel];v=windows[w];diff=(yy-bb).abs();v['abs']+=diff.sum((0,2,3,4));den=yy.abs().sum((0,2,3,4));den[0]=(yy[:,0]-20).abs().sum();v['den']+=den;hot=yy[:,0]>50;v['hot']+=torch.stack([diff[:,0][hot].sum(),(yy[:,0]-20).abs()[hot].sum(),hot.sum()]);v['cells']+=len(yy)*48*32*32;q=yy[:,1].sum((1,2,3))*.125;qb=bb[:,1].sum((1,2,3))*.125;v['qerr']+=(qb-q).abs().sum();v['qden']+=q.sum();v['pdose']+=(bb[:,5]-ambient).clamp_min(0).sum(0);v['tdose']+=(yy[:,5]-ambient).clamp_min(0).sum(0)
    rr=dict(case=c['case'],configuration=c['configuration'],split=c['split'],normalized_MAE=float(err.mean()/n),channel_normalized_MAE=(err/n).cpu().tolist())
    for w,v in windows.items():
     rr[w]=dict(channel_physical_MAE=(v['abs']/v['cells']).cpu().tolist(),channel_relative_L1_percent=(100*v['abs']/v['den'].clamp_min(1e-8)).cpu().tolist(),truth_hot_MAE_C=float(v['hot'][0]/v['hot'][2]) if v['hot'][2]>0 else None,truth_hot_relative_L1_percent=float(100*v['hot'][0]/v['hot'][1]) if v['hot'][1]>1e-8 else None,HRR_relative_L1_percent=float(100*v['qerr']/v['qden'].clamp_min(1e-8)),radiation_dose_relative_L1_percent=float(100*(v['pdose']-v['tdose']).abs().sum()/v['tdose'].sum().clamp_min(1e-8)))
    rows.append(rr)
  m.train();return rows
 def checkpoint(m,opt,sched,arm,epoch,pos,step,aggregate,history,label):
  state=dict(model=m.state_dict(),optimizer=opt.state_dict(),scheduler=sched.state_dict(),arm=arm,epoch=epoch,next_batch=pos,step=step,aggregate=aggregate,history=history,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),plan=plan,scales=scales.tolist());buf=io.BytesIO();torch.save(state,buf);upload(f'{arm}-{label}.pt',buf.getvalue());return state
 baseline=make('eight');oracle=make('oracle');c=train[0]
 with torch.no_grad():assert torch.equal(forward(baseline,'eight',c,0,3),forward(oracle,'oracle',c,0,3))
 upload('matched-initialization.json',json.dumps(dict(passed=True,oracle_initial_prediction_exact=True,base_weights_sha256=digest(baseline))).encode());del baseline,oracle;torch.cuda.empty_cache()
 for arm in ['source','single','eight','oracle']:
  pool=[c for c in train if c['case']==plan['single_case']] if arm=='single' else train;validation=[c for c in cs if c['split']=='validation'];evalpool=pool+validation;epochs=plan['epochs'][arm];windows=[(c,k,min(k+3,len(arrays[c['case']][1]))) for c in pool for k in range(0,len(arrays[c['case']][1]),3)];total_steps=epochs*len(windows)
  m=make(arm);opt=torch.optim.AdamW(m.parameters(),lr=.001,weight_decay=1e-5);sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=total_steps,eta_min=1e-5);history=[];start_epoch=0;start_pos=0;step=0;aggregate=dict(sum=0.,frames=0,channels=[0.]*6)
  resume=R/'data/resume'/f'{arm}.pt'
  if resume.exists():
   s=torch.load(resume,map_location='cuda',weights_only=False);assert s['arm']==arm and s['plan']==plan and s['scales']==scales.tolist();m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer']);sched.load_state_dict(s['scheduler']);start_epoch=s['epoch'];start_pos=s['next_batch'];step=s['step'];aggregate=s['aggregate'];history=s['history'];torch.set_rng_state(s['cpu_rng'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in s['cuda_rng']])
  report['initial_hashes'][arm]=digest(m);c,k,end=windows[0]
  with torch.no_grad():before=forward(m,arm,c,k,end).clone()
  # Model, optimizer and scheduler roundtrip; exact forward replay before optimizer use.
  buf=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),scheduler=sched.state_dict()),buf);buf.seek(0);s=torch.load(buf,map_location='cuda',weights_only=False);m.load_state_dict(s['model']);opt.load_state_dict(s['optimizer']);sched.load_state_dict(s['scheduler'])
  with torch.no_grad():assert torch.equal(before,forward(m,arm,c,k,end))
  upload(f'{arm}-resume-check.json',json.dumps(dict(passed=True,step=step,epoch=start_epoch,next_batch=start_pos)).encode())
  if step==0:
   initial=dict(epoch=0,step=0,rows=evaluate(m,arm,evalpool));history.append(initial);upload(f'{arm}-epoch-000.json',json.dumps(initial).encode())
  try:
   for epoch in range(start_epoch,epochs):
    order=np.random.default_rng(3501+epoch).permutation(len(windows));begin=start_pos if epoch==start_epoch else 0
    for pos in range(begin,len(order)):
     c,k,end=windows[order[pos]];p=forward(m,arm,c,k,end)
     if arm=='source':
      y=torch.tensor(qs[c['case']][k:end]/qscale,device='cuda')[:,None];loss=(p-y).abs().mean();per=None
     else:
      a,t=arrays[c['case']];y=torch.tensor(encode(a[k:end],c['wind_speed']),device='cuda');per=((p-y).abs()/sc).mean((0,2,3,4));loss=per.mean()
     assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();sched.step();step+=1;aggregate['sum']+=float(loss.detach())*(end-k);aggregate['frames']+=end-k
     if per is not None:aggregate['channels']=[u+v*(end-k) for u,v in zip(aggregate['channels'],per.detach().cpu().tolist())]
     if step%250==0:checkpoint(m,opt,sched,arm,epoch,pos+1,step,aggregate,history,f'step-{step:06}')
    rec=dict(epoch=epoch+1,step=step,mean_training_loss=aggregate['sum']/aggregate['frames'],mean_training_channel_loss=[v/aggregate['frames'] for v in aggregate['channels']] if arm!='source' else None,learning_rate=opt.param_groups[0]['lr'],rows=evaluate(m,arm,evalpool),elapsed_s=time.monotonic()-started);history.append(rec);upload(f'{arm}-epoch-{epoch+1:03}.json',json.dumps(rec).encode());aggregate=dict(sum=0.,frames=0,channels=[0.]*6);checkpoint(m,opt,sched,arm,epoch+1,0,step,aggregate,history,f'epoch-{epoch+1:03}');print(arm,epoch+1,rec['mean_training_loss'],flush=True)
   report['curves'][arm]=history;upload(f'{arm}-complete.json',json.dumps(dict(success=True,final_weights_sha256=digest(m),epochs=epochs,steps=step)).encode())
  except BaseException:
   try:checkpoint(m,opt,sched,arm,epoch,pos+1,step,aggregate,history,'interrupted')
   except Exception:pass
   raise
  del m,opt,sched;torch.cuda.empty_cache()
 report['elapsed_s']=time.monotonic()-started;report['input_hashes']=json.loads((R/'hashes.json').read_text());raw=json.dumps(report).encode();upload('report.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  upload('error.txt',traceback.format_exc().encode());raise
