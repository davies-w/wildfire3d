"""Local development comparison, per fixed tree type. No pair/test data, no cloud."""
import json,time,hashlib,argparse
import numpy as np
import torch
from torch import nn
from build import ROOT
from model_data import observation
ap=argparse.ArgumentParser();ap.add_argument('--epochs',type=int,default=400);ap.add_argument('--tag',default='');args=ap.parse_args();suffix=('-'+args.tag) if args.tag else '';
START=time.monotonic();torch.set_num_threads(1);torch.manual_seed(26)
out=ROOT/('data/single-dynamics'+suffix);out.mkdir(exist_ok=True)
freeze=json.loads((ROOT/'results/prediction-freeze.json').read_text())
for f,h in freeze['files'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
TT=np.arange(0,182,2)

def load(typ):
 ds=[]
 for c in json.loads((ROOT/'cases.json').read_text()):
  if c['family']!='single' or c['trees'][0]['type']!=typ:continue
  d=observation(c);s=d['state'].numpy();n=s.shape[1]
  y=np.column_stack([np.interp(TT,d['time'],s[:,j,k]) for k in range(2) for j in range(n)])
  ds.append(dict(case=c['case'],split=c['split'],y=y,u=np.array([c['strength'] if t+1<c['duration'] else 0 for t in TT[:-1]])))
 return ds,n

def metric(p,d,n):
 diff=abs(p[:,:n]-d['y'][:,:n]);active=(p[:,:n]>.08)|(d['y'][:,:n]>.08)
 return dict(case=d['case'],split=d['split'],temperature_MAE_C=float(diff.mean()*1000),active_union_temperature_MAE_C=float(diff[active].mean()*1000) if active.any() else None,mass_fraction_MAE=float(abs(p[:,n:]-d['y'][:,n:]).mean()),mass_bound_violations=int(((p[:,n:]< -1e-6)|(p[:,n:]>1+1e-6)).sum()),mass_increase_violations=int((np.diff(p[:,n:],axis=0)>1e-6).sum()),below_0C_violations=int((p[:,:n]<-.020001).sum()))
def score(rows,split='validation'):return float(np.mean([r['temperature_MAE_C']/1000+r['mass_fraction_MAE'] for r in rows if r['split']==split]))

class Recurrent(nn.Module):
 def __init__(self,n):
  super().__init__();self.n=n;self.cell=nn.GRUCell(2*n+1,32);self.head=nn.Linear(32,2*n)
  nn.init.normal_(self.head.weight,std=.01)
  with torch.no_grad():self.head.bias[:n].fill_(-3.9);self.head.bias[n:].fill_(-5.)
 def forward(self,u):
  b=u.shape[0];s=torch.cat([torch.zeros(b,self.n),torch.ones(b,self.n)],1);h=torch.zeros(b,32);states=[s]
  for j in range(u.shape[1]):
   h=self.cell(torch.cat([s,u[:,j,None]],1),h);q=self.head(h)
   temp=torch.nn.functional.softplus(q[:,:self.n])-.02 # >=0C; normalized (C-20)/1000
   mass=s[:,self.n:]*torch.exp(-.1*torch.sigmoid(q[:,self.n:]))
   s=torch.cat([temp,mass],1);states.append(s)
  return torch.stack(states,1)

report=dict(scope='Three separate fixed-geometry models, each four training and two existing validation exposures. No pairs/tests. Whole180s autonomous rollout. Outputs regional temperatures and wet+solid masses only; no heat/fuel/flame prediction.',selection='Temperature MAE/1000 + mass-fraction MAE, averaged equally over validation configurations. Existing validation reused; exploratory comparison, no new independent test.',constraints='Mass in[0,1], nonincreasing; temperature >=0C for these ambient20C experiments. Not energy conservation or complete physical validity.',types=[])
for typ in 'ABC':
 ds,n=load(typ);train=[d for d in ds if d['split']=='train'];initial=np.r_[np.zeros(n),np.ones(n)];_,_,v=np.linalg.svd(np.concatenate([d['y']-initial for d in train]),full_matrices=False);candidates=[];best=None
 for rank in [2,4,8,12]:
  basis=v[:rank].T
  for delay in [1,2,4]:
   X=[];Y=[]
   for d in train:
    z=(d['y']-initial)@basis
    for j in range(90):X.append(np.r_[np.concatenate([z[max(0,j-k)] for k in range(delay)]),d['u'][j],1]);Y.append(z[j+1])
   X=np.array(X);Y=np.array(Y)
   for ridge in [1e-3,.1,1]:
    op=np.linalg.solve(X.T@X+ridge*np.eye(X.shape[1]),X.T@Y);predictions=[]
    for d in ds:
     z=[np.zeros(rank)];p=[initial.copy()]
     for j in range(90):
      zz=np.r_[np.concatenate([z[max(0,j-k)] for k in range(delay)]),d['u'][j],1]@op
      yy=zz@basis.T+initial;yy[:n]=np.maximum(yy[:n],-.02);yy[n:]=np.clip(yy[n:],0,p[-1][n:]);p.append(yy);z.append((yy-initial)@basis)
     predictions.append(np.array(p))
    rows=[metric(p,d,n) for p,d in zip(predictions,ds)];sc=score(rows);candidate=dict(rank=rank,delay=delay,ridge=ridge,validation_score=sc);candidates.append(candidate)
    if best is None or sc<best[0]:best=(sc,candidate,rows,predictions,basis.copy(),op.copy())
 np.savez_compressed(out/f'{typ}-rom-weights.npz',basis=best[4],operator=best[5],initial=initial)
 for d,p in zip(ds,best[3]):np.savez_compressed(out/(d['case']+'-rom.npz'),time=TT,prediction=p,truth=d['y'])
 print(typ,'ROM',best[1],flush=True)
 # Full trajectory loss: every state/hidden value comes from the model, never teacher-forced.
 torch.manual_seed(26);m=Recurrent(n);opt=torch.optim.Adam(m.parameters(),lr=.003);U=torch.tensor(np.array([d['u'] for d in train]),dtype=torch.float32);Y=torch.tensor(np.array([d['y'] for d in train]),dtype=torch.float32);allU=torch.tensor(np.array([d['u'] for d in ds]),dtype=torch.float32)
 hist=[];bestnn=None;start=time.monotonic()
 for epoch in range(args.epochs+1):
  m.train();opt.zero_grad();p=m(U);loss=((p[:,:,:n]-Y[:,:,:n])**2).mean()+((p[:,:,n:]-Y[:,:,n:])**2).mean();loss.backward();nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
  if epoch%10==0 or epoch==args.epochs:
   m.eval()
   with torch.no_grad():ps=m(allU).numpy()
   rows=[metric(p,d,n) for p,d in zip(ps,ds)];sc=score(rows);hist.append(dict(epoch=epoch,training_loss=float(loss.detach()),validation_score=sc))
   if bestnn is None or sc<bestnn[0]:bestnn=(sc,epoch,rows,ps.copy(),{k:v.detach().clone() for k,v in m.state_dict().items()})
  if time.monotonic()-start>120:break
 torch.save(bestnn[4],out/f'{typ}-recurrent.pt')
 for d,p in zip(ds,bestnn[3]):np.savez_compressed(out/(d['case']+'-recurrent.npz'),time=TT,prediction=p,truth=d['y'])
 report['types'].append(dict(type=typ,rom=dict(selected=best[1],metrics=best[2],candidates=candidates),recurrent=dict(selected_epoch=bestnn[1],epochs_completed=epoch+1,parameters=sum(p.numel() for p in m.parameters()),metrics=bestnn[2],history=hist,fit_seconds=time.monotonic()-start)))
 (ROOT/('results/single-dynamics-comparison'+suffix+'.json')).write_text(json.dumps(report,indent=2));print(typ,'RECURRENT',bestnn[0],'epoch',bestnn[1],'elapsed',time.monotonic()-start,flush=True)
report['total_seconds']=time.monotonic()-START
(ROOT/('results/single-dynamics-comparison'+suffix+'.json')).write_text(json.dumps(report,indent=2))
