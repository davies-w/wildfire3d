"""Full development fit/evaluation, checkpointed; no FDS runs or test-set access."""
import os,json,time,io,tarfile,hashlib,urllib.request,urllib.parse,subprocess,sys,traceback,copy
from pathlib import Path
import numpy as np
import torch
from original_cnn import ROOT,load,cond,encode
from models import make
from previous_loss import objective
BUCKET='tmrw-wildfire-20261015-trial';PREFIX='gpu29/train01/'
def token():
 r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 return json.load(urllib.request.urlopen(r,timeout=20))['access_token']
def upload(name,data):
 u='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+name,safe='')
 r=urllib.request.Request(u,data=data,headers={'Authorization':'Bearer '+token(),'Content-Type':'application/octet-stream'},method='POST')
 urllib.request.urlopen(r,timeout=180).read()
def validate(m,cases):
 scores=[]
 with torch.no_grad():
  for c in cases:
   a,t=load(c);ss=[]
   for k in range(0,len(t),2):
    y=torch.from_numpy(encode(a[k:k+2],c['wind_speed'])).cuda();v=m(torch.from_numpy(cond(c,t[k:k+2])).cuda());ss.extend([float(objective(v,y))]*len(v))
   scores.append(float(np.mean(ss)))
 return float(np.mean(scores))
def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);torch.manual_seed(2902);rng=np.random.default_rng(2902)
 torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
 torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 cs=json.loads((ROOT/'cases.json').read_text());assert len(cs)==38 and all(c['split'] in ['train','validation'] for c in cs)
 manifest=json.loads((ROOT/'input-hashes.json').read_text())
 for n,h in manifest.items():
  p=ROOT/n; dig=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):dig.update(b)
  assert dig.hexdigest()==h,n
 upload('input-verification.json',json.dumps({'files':len(manifest),'verified':True}).encode())
 train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation'];m=make('heads').cuda();opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=.0001,weight_decay=1e-5)
 arrays=[load(c) for c in train];best=validate(m,val);state=copy.deepcopy(m.state_dict());selected=0;history=[dict(step=0,validation_score=best)];start=time.monotonic()
 def step():
  j=int(rng.integers(len(train)));c=train[j];a,t=arrays[j];ix=rng.integers(len(t),size=2);y=torch.from_numpy(encode(a[ix],c['wind_speed'])).cuda();v=m(torch.from_numpy(cond(c,t[ix])).cuda());loss=objective(v,y);assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
 def checkpoint(i):
  b=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),step=i,best_model=state,best=best,selected=selected,history=history,numpy_rng=rng.bit_generator.state,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),b);return b.getvalue()
 def restore(b):
  d=torch.load(io.BytesIO(b),map_location='cuda',weights_only=False);m.load_state_dict(d['model']);opt.load_state_dict(d['optimizer']);rng.bit_generator.state=d['numpy_rng'];torch.set_rng_state(d['cpu_rng'].cpu());torch.cuda.set_rng_state_all([x.cpu() for x in d['cuda_rng']])
 for i in range(1,3201):
  step()
  if i%800==0:
   score=validate(m,val);history.append(dict(step=i,validation_score=score));print('heads',i,score,flush=True)
   if score<best:best=score;state=copy.deepcopy(m.state_dict());selected=i
  if i%200==0:
   b=checkpoint(i);upload('checkpoint-%04d.pt'%i,b)
   if i==200:
    step();expected={k:v.detach().cpu().clone() for k,v in m.state_dict().items()};restore(b);step();delta=max(float((v.detach().cpu()-expected[k]).abs().max()) for k,v in m.state_dict().items());assert delta<1e-5,delta;restore(b);upload('resume-check.json',json.dumps({'max_next_step_weight_difference':delta,'scope':'in-process optimizer and RNG restore; not real Spot replacement'}).encode())
 m.load_state_dict(state);torch.save({k:v.cpu() for k,v in state.items()},ROOT/'data/models/heads.pt')
 report=dict(history=history,selected_step=selected,elapsed_s=time.monotonic()-start,device=torch.cuda.get_device_name(),parameters=sum(p.numel() for p in m.parameters()),trainable_parameters=sum(p.numel() for p in m.parameters() if p.requires_grad),training_cases=[c['case'] for c in train],selection_cases=[c['case'] for c in val],selection='Full 91-frame validation histories, previous physical loss; no test data',restart_note='Local unfinished fit had no checkpoint; repeated same 3200-step warm-start protocol on CUDA')
 (ROOT/'results/heads-training.json').write_text(json.dumps(report,indent=2));upload('heads.pt',(ROOT/'data/models/heads.pt').read_bytes());upload('heads-training.json',json.dumps(report,indent=2).encode())
 for name in ['previous','bound_only','bounded','heads','strength_only','interpolation']:
  subprocess.run([sys.executable,str(ROOT/'evaluate.py'),name,'--device','cuda'],check=True)
  upload(name+'-evaluation.json',(ROOT/f'results/{name}-evaluation.json').read_bytes())
 with tarfile.open(ROOT/'outputs.tar','w') as tar:
  for rel in ['results','data/models/heads.pt','data/validation_predictions']:tar.add(ROOT/rel,arcname=rel)
 upload('outputs.tar',(ROOT/'outputs.tar').read_bytes());upload('complete.json',json.dumps({'success':True,'training':report,'output_sha256':hashlib.sha256((ROOT/'outputs.tar').read_bytes()).hexdigest()}).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
