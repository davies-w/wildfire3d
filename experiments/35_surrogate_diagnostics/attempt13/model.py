"""Residual state transition MLP; raw outputs, no loss-time physical clamp."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,nstate=52,nexternal=13):
  super().__init__();self.net=nn.Sequential(nn.Linear(nstate+nexternal,128),nn.SiLU(),nn.Linear(128,128),nn.SiLU(),nn.Linear(128,nstate))
  nn.init.zeros_(self.net[-1].weight);nn.init.zeros_(self.net[-1].bias)
 def forward(self,state,external):return state+self.net(torch.cat([state,external],-1))*(external[:,-1:])
def normalize_fit(raw,mask,ids,config,scale):
 # Configuration-balanced, training-only moments. Replicas divide their configuration weight.
 x=torch.asinh(raw/scale);w=mask[ids].clone()
 for c in torch.unique(config[ids]):w[config[ids]==c]/=(config[ids]==c).sum()
 den=w.sum((0,1)).clamp_min(1);mean=(x[ids]*w).sum((0,1))/den;std=(((x[ids]-mean).square()*w).sum((0,1))/den).sqrt().clamp_min(.05)
 return mean,std
