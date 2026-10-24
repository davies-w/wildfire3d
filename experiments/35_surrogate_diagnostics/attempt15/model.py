"""Small residual finite-history transition, with no output clipping."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self):
  super().__init__();self.net=nn.Sequential(nn.Linear(21,64),nn.SiLU(),nn.Linear(64,64),nn.SiLU(),nn.Linear(64,3));nn.init.zeros_(self.net[-1].weight);nn.init.zeros_(self.net[-1].bias)
 def forward(self,history,external):
  return history[:,-1]+self.net(torch.cat([history.flatten(1),external],-1))*external[:,-1:]
def normalize_fit(raw,ids,config,scale):
 x=torch.asinh(raw/scale);means=[];seconds=[]
 for c in torch.unique(config[ids]):
  v=x[ids[config[ids]==c]];means.append(v.mean((0,1)));seconds.append(v.square().mean((0,1)))
 mean=torch.stack(means).mean(0);std=(torch.stack(seconds).mean(0)-mean.square()).clamp_min(0).sqrt().clamp_min(.05)
 return mean,std
