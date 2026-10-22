"""Warm-start matched development fits; whole validation histories select checkpoints."""
import argparse,json,time,copy
import numpy as np
import torch
from original_cnn import ROOT,load,cond,encode
from previous_loss import objective
from models import make

def validate(m,cases,device):
 scores=[]
 with torch.no_grad():
  for c in cases:
   a,t=load(c);ss=[]
   for k in range(0,len(t),2):
    y=torch.from_numpy(encode(a[k:k+2],c['wind_speed'])).to(device);p=m(torch.from_numpy(cond(c,t[k:k+2])).to(device));ss.extend([float(objective(p,y))]*len(p))
   scores.append(float(np.mean(ss)))
 return float(np.mean(scores))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['bounded','heads']);ap.add_argument('--steps',type=int,default=3200);args=ap.parse_args();torch.manual_seed(2902);rng=np.random.default_rng(2902);device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu');cs=json.loads((ROOT/'cases.json').read_text());train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation'];m=make(args.kind).to(device);opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=.0001,weight_decay=1e-5);arrays=[load(c) for c in train];best=validate(m,val,device);state=copy.deepcopy(m.state_dict());selected=0;history=[dict(step=0,validation_score=best)];start=time.monotonic();print(args.kind,0,best,flush=True)
 for step in range(1,args.steps+1):
  j=int(rng.integers(len(train)));c=train[j];a,t=arrays[j];ix=rng.integers(len(t),size=2);y=torch.from_numpy(encode(a[ix],c['wind_speed'])).to(device);p=m(torch.from_numpy(cond(c,t[ix])).to(device));l=objective(p,y);opt.zero_grad();l.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
  if step%800==0 or step==args.steps:
   score=validate(m,val,device);history.append(dict(step=step,validation_score=score));print(args.kind,step,score,flush=True)
   if score<best:best=score;state=copy.deepcopy(m.state_dict());selected=step
   (ROOT/f'results/{args.kind}-progress.json').write_text(json.dumps(dict(history=history,elapsed_s=time.monotonic()-start),indent=2))
 m.load_state_dict(state);torch.save(state,ROOT/f'data/models/{args.kind}.pt');(ROOT/f'results/{args.kind}-training.json').write_text(json.dumps(dict(history=history,selected_step=selected,elapsed_s=time.monotonic()-start,parameters=sum(p.numel() for p in m.parameters()),trainable_parameters=sum(p.numel() for p in m.parameters() if p.requires_grad),training_cases=[c['case'] for c in train],selection_cases=[c['case'] for c in val],selection='Full91-frame validation histories, previous physical loss; no test data'),indent=2));print('DONE',args.kind,flush=True)
if __name__=='__main__':main()
