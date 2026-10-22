import time,json,copy
import numpy as np
import torch
from models import Strength
from original_cnn import ROOT
z=np.load(ROOT/'data/scalar_targets.npz');torch.manual_seed(2901);m=Strength();opt=torch.optim.AdamW(m.parameters(),lr=.002,weight_decay=1e-5);x=torch.from_numpy(z['x']);y=torch.from_numpy(z['logq']);train=z['split']=='train';val=~train;xt=x[train];yt=y[train];xv=x[val];yv=y[val];best=1e9;history=[];start=time.monotonic()
def obj(p,y):return (p-y).square().mean()+.1*((torch.expm1(p.clamp(max=18))-torch.expm1(y)).abs()/(torch.expm1(y)+100)).mean()
for step in range(1,8001):
 ix=torch.randint(len(xt),(256,));p=m(xt[ix]);l=obj(p,yt[ix]);opt.zero_grad();l.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
 if step%500==0:
  with torch.no_grad():score=float(obj(m(xv),yv))
  history.append(dict(step=step,validation_score=score))
  if score<best:best=score;state=copy.deepcopy(m.state_dict());selected=step
m.load_state_dict(state);torch.save(state,ROOT/'data/models/strength.pt');(ROOT/'results/strength-training.json').write_text(json.dumps(dict(selected_step=selected,history=history,elapsed_s=time.monotonic()-start,train_configurations=32,validation_configurations=6),indent=2));print('Strength trained',selected,best,flush=True)
