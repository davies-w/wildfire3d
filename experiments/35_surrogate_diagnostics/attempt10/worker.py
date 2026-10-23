"""Cloud-only continuous-field fit; fixed U-Net, full validation every epoch."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import torch,numpy as np,json,io,time,hashlib,traceback,signal,copy
from pathlib import Path
from model import FieldUNet,encode,physical,channel_losses
from metrics import statistics,summarize_case,aggregate
from runtime import upload
R=Path(__file__).parent

def digest(m):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
def send(n,x):upload(n,json.dumps(x,allow_nan=False).encode())
def main():
 assert torch.cuda.is_available(),'Cloud GPU only: no laptop fitting';torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False
 plan=json.loads((R/'coverage-plan.json').read_text());cases=json.loads((R/'cases.json').read_text());train=[i for i,c in enumerate(cases) if c['split']=='train'];val=[i for i,c in enumerate(cases) if c['split']=='validation'];assert len(train)==8 and len(val)==40
 scales=torch.tensor(json.loads((R/'scales.json').read_text())['encoded_std'],device='cuda');assert (scales>=.04999).all()
 shape=(48,32,32);coords=np.stack(np.meshgrid(*[(np.arange(n)+.5)/n*2-1 for n in shape],indexing='ij')).astype('float32');geoms=np.load(R/'data/geometries.npz');density_scale=max(float(geoms[cases[i]['case']].max()) for i in train)
 raw=torch.empty((len(cases),91,6,*shape),device='cuda');targets=torch.empty_like(raw);static=[];times=[]
 for i,c in enumerate(cases):
  a=np.load(R/'data/fields'/(c['case']+'.npy'));assert a.shape==(91,6,*shape) and np.isfinite(a).all();raw[i].copy_(torch.from_numpy(a));targets[i].copy_(encode(raw[i],c['wind_speed']));del a
  t=np.load(R/'data/fields'/(c['case']+'-time.npy'));times.append(t);angle=np.radians(c['angle_deg']);cond=np.array([c['wind_speed']/5,c['moisture']/.3,c['loading_multiplier']/1.3,c['crown_height_m']/10,np.cos(angle),np.sin(angle)],np.float32)
  static.append(np.concatenate([geoms[c['case']]/density_scale,coords,np.broadcast_to(cond[:,None,None,None],(6,*shape))]))
 static=torch.from_numpy(np.stack(static)).cuda();ts=torch.tensor(np.stack(times),device='cuda',dtype=torch.float32);winds=torch.tensor([c['wind_speed'] for c in cases],device='cuda')
 def inp(ci,fi):return torch.cat([static[ci],(ts[ci,fi]/90-1)[:,None,None,None,None].expand(-1,1,*shape)],1)
 started=time.monotonic();stop=[False];signal.signal(signal.SIGTERM,lambda *args:stop.__setitem__(0,True))
 def evaluate(m,arm,epoch,ids,baseline=False):
  m.eval();rows=[];details=[];eb=plan['evaluation_batch_size']
  with torch.no_grad():
   for i,c in enumerate(cases):
    blocks=[]
    for k in range(0,91,eb):
     fi=list(range(k,min(k+eb,91)));ci=[i]*len(fi);w=winds[ci,None,None,None];truth=raw[i,fi]
     if baseline:
      a=torch.zeros_like(truth);a[:,0]=20;a[:,2]=c['wind_speed'];a[:,5]=raw[i,0,5].median();p=encode(a,w)
     else:p=m(inp(ci,fi))
     blocks.append(statistics(p,targets[i,fi],truth,w,scales))
    v=np.concatenate(blocks);rows.append(summarize_case(v,times[i]));details.append(v)
  summary={s:aggregate(rows,cases,ix) for s,ix in [('train',ids),('validation',val)]}
  rec=dict(arm=arm,epoch=epoch,summary=summary,elapsed_s=time.monotonic()-started,case_metrics=[dict(case=c['case'],configuration=c['configuration'],split=c['split'],windows=row) for c,row in zip(cases,rows)])
  send(f'{arm}-epoch-{epoch:03}.json',rec);b=io.BytesIO();np.savez_compressed(b,statistics=np.stack(details),time=np.stack(times),case=np.array([c['case'] for c in cases]));upload(f'{arm}-epoch-{epoch:03}-statistics.npz',b.getvalue());m.train();return rec
 states={};initial_hashes=[]
 for arm in plan['arms']:
  torch.manual_seed(plan['seed']);m=FieldUNet().cuda();opt=torch.optim.AdamW(m.parameters(),lr=plan['learning_rate'],weight_decay=plan['weight_decay']);ids=train if arm=='eight' else [next(i for i,c in enumerate(cases) if c['case']==plan['single_case'])]
  s=dict(model=m,optimizer=opt,ids=ids,next_epoch=0,next_batch=0,aggregate=[0.,0],step=0,history=[],plateau_count=0,reason='running',best=float('inf'),selected_epoch=None,best_model=None,last_case_metrics=None,initial_sha256=digest(m))
  rp=R/'data/resume'/(arm+'.pt')
  if rp.exists():
   z=torch.load(rp,map_location='cuda',weights_only=False);assert z['plan']==plan and z['arm']==arm;m.load_state_dict(z['model']);opt.load_state_dict(z['optimizer'])
   for key in ['next_epoch','next_batch','aggregate','step','history','plateau_count','reason','best','selected_epoch','best_model','last_case_metrics','initial_sha256']:s[key]=z[key]
   torch.set_rng_state(z['cpu_rng'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in z['cuda_rng']])
  initial_hashes.append(s['initial_sha256']);states[arm]=s
 assert len(set(initial_hashes))==1
 def checkpoint(arm,label):
  s=states[arm];b=io.BytesIO();z={k:v for k,v in s.items() if k not in ['model','optimizer','ids']};z.update(model=s['model'].state_dict(),optimizer=s['optimizer'].state_dict(),plan=plan,arm=arm,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all());torch.save(z,b);upload(f'{arm}-{label}.pt',b.getvalue())
 # Check actual CUDA gradients, serialization replay, and initial predictions; reset optimizer afterward.
 for arm,s in states.items():
  if s['history']:continue
  m,opt=s['model'],s['optimizer'];saved=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict()),saved);ci=[train[0]];fi=[15]
  terms,_=channel_losses(m(inp(ci,fi)),targets[ci,fi],scales);loss=terms.mean();opt.zero_grad();loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for p in m.parameters());assert m.out.bias.grad[1].abs()>0;opt.step()
  with torch.no_grad():before=m(inp(ci,fi)).clone()
  b=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict()),b);b.seek(0);z=torch.load(b,map_location='cuda',weights_only=False);m.load_state_dict(z['model']);opt.load_state_dict(z['optimizer'])
  with torch.no_grad():assert torch.equal(before,m(inp(ci,fi)))
  saved.seek(0);z=torch.load(saved,map_location='cuda',weights_only=False);m.load_state_dict(z['model']);opt.load_state_dict(z['optimizer']);assert digest(m)==s['initial_sha256']
  send(arm+'-cuda-check.json',dict(passed=True,initial_model_sha256=s['initial_sha256'],parameters=sum(p.numel() for p in m.parameters()),unclamped_HRR_gradient_verified=True))
  rec=evaluate(m,arm,0,s['ids']);s['last_case_metrics']=rec['case_metrics'];s['history'].append({k:v for k,v in rec.items() if k!='case_metrics'});s['best']=rec['summary']['validation']['all']['objective_MSE'];s['selected_epoch']=0;s['best_model']={k:v.detach().cpu().clone() for k,v in m.state_dict().items()};checkpoint(arm,'epoch-000')
 if all(s['step']==0 for s in states.values()):evaluate(states['eight']['model'],'background_baseline',0,train,baseline=True)
 assert states['single']['history'][0]['summary']['validation']==states['eight']['history'][0]['summary']['validation']
 send('initialization.json',dict(passed=True,hashes=initial_hashes,geometry_scale=density_scale,validation_cases=len(val),input_time=True,independent_optimizers=True))
 def plateau(s):
  history=s['history'];stable=True;deltas={}
  for split in ['train','validation']:
   for key in ['objective_MSE','hot_temperature_relative_L1_percent','total_HRR_relative_L1_percent']:
    a=[h['summary'][split]['post_source'][key] for h in history[-20:-10]];b=[h['summary'][split]['post_source'][key] for h in history[-10:]]
    if any(v is None for v in a+b):stable=False;continue
    old,new=float(np.mean(a)),float(np.mean(b));delta=abs(new-old);tol=max(1e-4,.01*abs(old));stable &= delta<tol;deltas[split+'/'+key]=dict(before=old,after=new,tolerance=tol)
  return stable,deltas
 # Interleave arms by epoch so both make progress within the same cloud deadline.
 for epoch in range(min(s['next_epoch'] for s in states.values()),plan['maximum_epochs']):
  for arm,s in states.items():
   if s['reason']!='running' or s['next_epoch']>epoch:continue
   m,opt=s['model'],s['optimizer'];pairs=np.array([(i,j) for i in s['ids'] for j in range(91)]);pairs=pairs[np.random.default_rng(plan['seed']+epoch).permutation(len(pairs))];batch=plan['batch_size'];steps=(len(pairs)+batch-1)//batch
   try:
    for pos in range(s['next_batch'],steps):
     ci,fi=pairs[pos*batch:(pos+1)*batch].T.tolist();loss=channel_losses(m(inp(ci,fi)),targets[ci,fi],scales)[0].mean();assert torch.isfinite(loss);opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();s['step']+=1;s['next_batch']=pos+1;s['aggregate'][0]+=float(loss.detach())*len(ci);s['aggregate'][1]+=len(ci)
     if s['step']%250==0:checkpoint(arm,f'step-{s["step"]:06}')
     if stop[0] or time.monotonic()-started>plan['soft_deadline_s']:
      for key in states:checkpoint(key,'deadline')
      send('partial.json',dict(success=False,reason='deadline_not_convergence',arms={key:dict(epoch=v['next_epoch'],next_batch=v['next_batch'],updates=v['step']) for key,v in states.items()}));return
    assert s['aggregate'][1]==len(pairs)
    rec=evaluate(m,arm,epoch+1,s['ids']);s['last_case_metrics']=rec['case_metrics'];rec['training_minibatch_MSE']=s['aggregate'][0]/s['aggregate'][1];s['history'].append({k:v for k,v in rec.items() if k!='case_metrics'});s['aggregate']=[0.,0];s['next_epoch']=epoch+1;s['next_batch']=0
    score=rec['summary']['validation']['all']['objective_MSE']
    if score<s['best']:s['best']=score;s['selected_epoch']=epoch+1;s['best_model']={k:v.detach().cpu().clone() for k,v in m.state_dict().items()}
    if epoch+1>=plan['minimum_epochs'] and (epoch+1)%10==0:
     stable,deltas=plateau(s);s['plateau_count']=s['plateau_count']+1 if stable else 0;send(f'{arm}-plateau-{epoch+1:03}.json',dict(stable=bool(stable),consecutive=s['plateau_count'],deltas=deltas))
     if s['plateau_count']>=3:s['reason']='empirical_plateau_not_necessarily_good_fit'
    checkpoint(arm,f'epoch-{epoch+1:03}');print('EPOCH',arm,epoch+1,'TRAIN',rec['summary']['train']['post_source'],'VAL',rec['summary']['validation']['post_source'],flush=True)
   except BaseException:
    try:checkpoint(arm,'interrupted')
    except Exception:pass
    raise
  if all(s['reason']!='running' for s in states.values()):break
 reports=[];projections={}
 for arm,s in states.items():
  if s['reason']=='running':s['reason']='maximum_epochs_not_convergence'
  final=s['history'][-1];s['model'].load_state_dict(s['best_model']);selected=evaluate(s['model'],arm+'-selected',s['selected_epoch'],s['ids']);gates=[];final_gates=[]
  for i in s['ids']:
   row=selected['case_metrics'][i]['windows']['post_source'];limits=plan['fit_gate'];checks={k:row[k] is not None and row[k]<=limit for k,limit in [(k[:-4],v) for k,v in limits.items() if k.endswith('_max')]};gates.append(dict(case=cases[i]['case'],passed=all(checks.values()),checks=checks,metrics=row))
   row=s['last_case_metrics'][i]['windows']['post_source'];checks={k:row[k] is not None and row[k]<=limit for k,limit in [(k[:-4],v) for k,v in limits.items() if k.endswith('_max')]};final_gates.append(dict(case=cases[i]['case'],passed=all(checks.values()),checks=checks,metrics=row))
  report=dict(arm=arm,reason=s['reason'],initial_model_sha256=s['initial_sha256'],epochs=final['epoch'],selected_epoch=s['selected_epoch'],best_validation_objective=s['best'],final=final,selected={k:v for k,v in selected.items() if k!='case_metrics'},fit_gate=gates,final_fit_gate=final_gates,all_final_training_cases_passed=all(g['passed'] for g in final_gates),history=s['history']);send(arm+'-report.json',report);reports.append(report)
  b=io.BytesIO();torch.save(dict(model=s['best_model'],plan=plan,arm=arm,epoch=s['selected_epoch']),b);upload(arm+'-selected.pt',b.getvalue())
  with torch.no_grad():
   for i in [train[0],val[0]]:
    fi=[5,10,15,30];ci=[i]*4;pred=physical(s['model'](inp(ci,fi)),winds[ci,None,None,None]);projections[arm+'_'+cases[i]['case']]=pred[:,[0,1]].amax(3).cpu().numpy();projections['truth_'+cases[i]['case']]=raw[i,fi][:,[0,1]].amax(3).cpu().numpy()
 b=io.BytesIO();np.savez_compressed(b,**projections);upload('projections.npz',b.getvalue());data=json.dumps(dict(plan=plan,arms=reports,elapsed_s=time.monotonic()-started),allow_nan=False).encode();upload('report.json',data);send('complete.json',dict(success=True,report_sha256=hashlib.sha256(data).hexdigest()))
if __name__=='__main__':
 try:main()
 except BaseException:upload('error.txt',traceback.format_exc().encode());raise
