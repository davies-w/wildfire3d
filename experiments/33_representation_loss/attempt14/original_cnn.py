"""Conditional 3D CNN: inputs only wind, ignition angle and requested time."""
import json,math,hashlib,time,copy
from pathlib import Path
import numpy as np
import torch
from torch import nn
from deterministic_interpolation import double_trilinear
from torch.nn import functional as F
ROOT=Path(__file__).parent
torch.set_num_threads(4)
def cond(c,t):
 t=np.asarray(t);a=math.radians(c['angle_deg']);s=t/180
 return np.stack([np.full_like(s,c['wind_speed']/5),np.full_like(s,math.cos(a)),np.full_like(s,math.sin(a)),s,np.sin(s*np.pi),np.cos(s*np.pi),np.sin(s*2*np.pi),np.cos(s*2*np.pi)],axis=-1).astype('float32')
def encode(a,w):
 b=np.array(a,dtype='float32',copy=True)
 b[:,0]=np.arcsinh((b[:,0]-20)/100);b[:,1]=np.log1p(np.maximum(b[:,1],0)/10)
 b[:,2]=(b[:,2]-w)/5;b[:,3:5]/=5;b[:,5]=np.log1p(np.maximum(b[:,5],0)/2)
 return b
def decode(b,w):
 a=np.array(b,dtype='float32',copy=True)
 a[:,0]=20+100*np.sinh(np.clip(a[:,0],-5,5));a[:,1]=10*np.expm1(np.clip(a[:,1],0,10));a[:,2]=a[:,2]*5+w;a[:,3:5]*=5;a[:,5]=2*np.expm1(np.clip(a[:,5],0,10));return a
class CNN(nn.Module):
 def __init__(self):
  super().__init__();self.fc=nn.Sequential(nn.Linear(8,96),nn.SiLU(),nn.Linear(96,16*6*4*4))
  self.layers=nn.ModuleList([nn.Conv3d(16,16,3,padding=1),nn.Conv3d(16,12,3,padding=1),nn.Conv3d(12,8,3,padding=1)]);self.out=nn.Conv3d(8,6,3,padding=1)
 def forward(self,c):
  x=self.fc(c).reshape(-1,16,6,4,4)
  for layer in self.layers:x=F.silu(layer(double_trilinear(x)))
  return self.out(x)
def load(c):
 return np.load(ROOT/'data/fields'/(c['case']+'.npy'),mmap_mode='r'),np.load(ROOT/'data/fields'/(c['case']+'-time.npy'))
def loss(p,y):
 # Per-channel transformed loss, emphasizing warm/fire cells without ignoring the background.
 weights=1+4*(y[:,0:1]>.3).float()+4*(y[:,1:2]>.2).float()
 return ((p-y).square()*weights).mean()
def prediction(model,c,t):
 out=[]
 with torch.no_grad():
  for i in range(0,len(t),2):out.append(decode(model(torch.from_numpy(cond(c,t[i:i+2])).to(next(model.parameters()).device)).cpu().numpy(),c['wind_speed']))
 return np.concatenate(out)
def main():
 cases=json.loads((ROOT/'cases.json').read_text());train=sorted([c for c in cases if c['split']=='train'],key=lambda c:c['training_rank']);val=[c for c in cases if c['split']=='validation'];tests=[c for c in cases if c['split']=='test']
 out=ROOT/'data/models';out.mkdir(exist_ok=True);pred=ROOT/'data/predictions';pred.mkdir(exist_ok=True)
 report=[]
 for n in [8,16,32]:
  torch.manual_seed(2700);rng=np.random.default_rng(2700);device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu');model=CNN().to(device);opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=1e-5)
  arrays=[load(c) for c in train[:n]];best=float('inf');history=[];started=time.monotonic()
  steps=400*n
  for step in range(steps+1):
   j=int(rng.integers(n));c=train[j];a,t=arrays[j];ix=rng.integers(0,len(t),size=2)
   y=torch.from_numpy(encode(a[ix],c['wind_speed'])).to(device);p=model(torch.from_numpy(cond(c,t[ix])).to(device));l=loss(p,y);opt.zero_grad();l.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
   if step%max(200,25*n)==0:
    scores=[]
    with torch.no_grad():
     for v in val:
      av,tv=load(v)
      for k in [5,10,15,25,45,75,90]:
       k=min(k,len(tv)-1);yv=torch.from_numpy(encode(av[k:k+1],v['wind_speed'])).to(device);pv=model(torch.from_numpy(cond(v,tv[k:k+1])).to(device));scores.append(float(loss(pv,yv)))
    score=float(np.mean(scores));history.append(dict(step=step,train_loss=float(l),validation_loss=score));print(n,step,score,flush=True)
    if score<best:best=score;state=copy.deepcopy(model.state_dict());selected=step
    if step>=200*n and step-selected>=100*n:break
  model.load_state_dict(state);torch.save(state,out/f'cnn_{n}.pt');start=time.monotonic()
  for c in tests:
   t=np.arange(0,181,2,dtype=float);np.save(pred/f"cnn_{n}_{c['case']}.npy",prediction(model,c,t))
  prediction_seconds=(time.monotonic()-start)/len(tests)
  reconstruction=[]
  with torch.no_grad():
   for c in train[:n]+val:
    av,tv=load(c);ids=np.arange(0,len(tv),6);truth=np.array(av[ids]);forecast=prediction(model,c,tv[ids]);mask=(truth[:,0]>50)|(forecast[:,0]>50)
    reconstruction.append(dict(case=c['case'],split=c['split'],temperature_MAE_C=float(abs(truth[:,0]-forecast[:,0]).mean()),hot_union_temperature_MAE_C=float(abs(truth[:,0]-forecast[:,0])[mask].mean()) if mask.any() else None,HRRPUV_MAE_kW_m3=float(abs(truth[:,1]-forecast[:,1]).mean()),sampling='every sixth volume frame; full spatial grid'))
  report.append(dict(training_configurations=n,device=str(device),parameters=sum(p.numel() for p in model.parameters()),selected_step=selected,optimization_steps_completed=step,maximum_optimization_steps=steps,history=history,total_fit_and_diagnostic_seconds=time.monotonic()-started,seconds_per_test=prediction_seconds,reconstruction=reconstruction))
  (ROOT/'results/training.json').write_text(json.dumps(report,indent=2))
 # Interpolation baseline uses whole TRAINING fields only; same parameter neighborhood for all times.
 for n in [8,16,32]:
  for c in tests:
   features=lambda q:np.array([q['wind_speed']/4,math.cos(math.radians(q['angle_deg'])),math.sin(math.radians(q['angle_deg']))])
   distances=np.array([np.linalg.norm(features(c)-features(q)) for q in train[:n]]);idx=np.argsort(distances)[:3];weights=1/np.maximum(distances[idx],.01)**2;weights/=weights.sum();base=None
   for j,w in zip(idx,weights):
    a,t=load(train[j]);wanted=np.arange(0,181,2);ix=np.abs(t[:,None]-wanted).argmin(axis=0);term=np.array(a[ix]);term[:,2]-=train[j]['wind_speed'];term*=w;base=term if base is None else base+term
   base[:,2]+=c['wind_speed']
   np.save(pred/f"interpolation_{n}_{c['case']}.npy",base)
 files=[*out.glob('*.pt'),*pred.glob('*.npy'),ROOT/'cnn.py',ROOT/'predict.py',ROOT/'cases.json',ROOT/'fields.py',ROOT/'evaluate.py',ROOT/'audit_pilot_corners.py',ROOT/'results/input-freeze.json']
 freeze=dict(created_unix=time.time(),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},cases=[c['case'] for c in tests],selection='validation only; 8/16/32 results all reported; test not opened')
 (ROOT/'results/prediction-freeze.json').write_text(json.dumps(freeze,indent=2));print('FROZEN',flush=True)
if __name__=='__main__':main()
