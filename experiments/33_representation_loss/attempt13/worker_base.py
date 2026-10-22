"""Three controlled training arms; development-only capacity diagnostic."""
import json,time,io,copy,hashlib,traceback,urllib.request,urllib.parse,os
from pathlib import Path
import numpy as np,torch
from original_cnn import cond,encode,load
from geometry_model import GeometryCNN,features
from previous_loss import objective
from losses import revised
from models import SpatialHeads
from snapshot_evaluation import metrics
R=Path(__file__).parent
PREFIX='repair33/pilot13/'
def upload(n,data):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(req,timeout=20))['access_token'];url='https://storage.googleapis.com/upload/storage/v1/b/tmrw-wildfire-20261015-trial/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+n,safe='');urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'},method='POST'),timeout=180).read()
def inputs(c,t,g,device):
 f=np.concatenate([cond(c,t),np.repeat(features(g)[None],len(t),0),np.full((len(t),1),(c['moisture']-.12)/.18,np.float32)],1)
 src=np.zeros((48,32,32),np.float32);angles=np.deg2rad(c['angle_deg']-30+60*(np.arange(1600)+.5)/1600);ix=np.array([(8+1.2*np.cos(angles))/.5,(8+1.2*np.sin(angles))/.5,np.full(1600,2.1/.5)]).astype(int);np.add.at(src,tuple(ix),1);src/=src.max()
 return torch.from_numpy(f).to(device),torch.from_numpy(np.repeat(g[None],len(t),0)).to(device),torch.from_numpy(src[None,None]*np.array(t<20.1,np.float32)[:,None,None,None,None]).to(device)
def predict(model,arm,c,t,g,device):
 x,d,s=inputs(c,t,g,device);return model(x,d,s) if arm=='spatial_heads' else model(x)
def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);cs=json.loads((R/'cases.json').read_text());assert all(c['split'] in ['train','validation'] for c in cs);geoms=dict(np.load(R/'data/geometries.npz'));arrays={c['case']:load(c) for c in cs};train=[c for c in cs if c['split']=='train'];device='cuda';reports={};rows=[];started=time.monotonic()
 # Identical per-step case/frame schedule for every arm; one seed per configuration.
 rng=np.random.default_rng(3301);schedule=[]
 for step in range(12000):
  c=train[int(rng.integers(len(train)))];a,t=arrays[c['case']]
  # Equal source-on, active post-source and late windows instead of mostly cold frames.
  lo,hi=[(0,10),(10,30),(30,len(t)-2)][step%3];k=int(rng.integers(lo,max(lo+1,hi)));schedule.append((c,k))
 def evaluate(model,arm,tag):
  model.eval();out=[]
  with torch.no_grad():
   for c in cs:
    a,t=arrays[c['case']];pp=[]
    for k in range(0,len(t),3):pp.append(predict(model,arm,c,t[k:k+3],geoms[c['case']],device).cpu().numpy())
    from original_cnn import decode
    out.append(dict(arm=arm,stage=tag,case=c['case'],split=c['split'],**metrics(np.array(a),decode(np.concatenate(pp),c['wind_speed']),t)))
  model.train();return out
 for arm in ['current','loss_only','spatial_heads']:
  torch.manual_seed(3301);model=(SpatialHeads() if arm=='spatial_heads' else GeometryCNN()).to(device)
  if arm!='spatial_heads':model.load_state_dict(torch.load(R/'data/initial_snapshot.pt',map_location=device,weights_only=True))
  opt=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=1e-5);lossfn=objective if arm=='current' else revised;history=[];armstart=time.monotonic();rows+=evaluate(model,arm,'initial')
  resume=R/'data/resume'/f'{arm}.pt';start_step=0
  if resume.exists():
   saved=torch.load(resume,map_location=device,weights_only=False);assert saved['arm']==arm and saved['schedule_seed']==3301
   model.load_state_dict(saved['model']);opt.load_state_dict(saved['optimizer']);start_step=saved['step'];torch.set_rng_state(saved['cpu_rng'].cpu());torch.cuda.set_rng_state_all([x.cpu() for x in saved['cuda_rng']])
  # Exercise serialization and restore before learning on the actual CUDA worker.
  c,k=schedule[start_step if start_step<12000 else 11999];a,t=arrays[c['case']]
  with torch.no_grad():before=predict(model,arm,c,t[k:k+3],geoms[c['case']],device).clone()
  check=io.BytesIO();torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict()),check);check.seek(0);restored=torch.load(check,map_location=device,weights_only=False);model.load_state_dict(restored['model']);opt.load_state_dict(restored['optimizer'])
  with torch.no_grad():after=predict(model,arm,c,t[k:k+3],geoms[c['case']],device)
  assert torch.equal(before,after),'checkpoint roundtrip changed prediction'
  upload(arm+'-resume-check.json',json.dumps(dict(passed=True,device=device,start_step=start_step,scope='model and optimizer serialization; exact forward replay before training')).encode())
  for step,(c,k) in enumerate(schedule,1):
   if step<=start_step or arm=='current':continue
   a,t=arrays[c['case']];p=predict(model,arm,c,t[k:k+3],geoms[c['case']],device);y=torch.from_numpy(encode(a[k:k+3],c['wind_speed'])).to(device);loss=lossfn(p,y);assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
   if step%500==0:
    history.append(dict(step=step,loss=float(loss.detach()),elapsed_s=time.monotonic()-armstart));buf=io.BytesIO();torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),step=step,arm=arm,schedule_seed=3301,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),buf);upload(f'{arm}-checkpoint-{step}.pt',buf.getvalue());print(arm,step,float(loss.detach()),flush=True)
  rows+=evaluate(model,arm,'final');reports[arm]=dict(history=history,elapsed_s=time.monotonic()-armstart,parameters=sum(p.numel() for p in model.parameters()));upload(arm+'-results.json',json.dumps(dict(rows=[x for x in rows if x['arm']==arm],training=reports[arm])).encode());del model,opt;torch.cuda.empty_cache()
 result=dict(rows=rows,training=reports,elapsed_s=time.monotonic()-started,scope='12 deliberately stratified training configurations and8 development-validation configurations; not independent test. Current/loss-only warm-start from exp32; spatial arm starts fresh.12000 total updates x3 consecutive frames each. No FDS run or former test data.',input_hashes=json.loads((R/'hashes.json').read_text()));raw=json.dumps(result,indent=2).encode();upload('report.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
