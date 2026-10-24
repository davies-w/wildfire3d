"""Matched finite-history and gated-memory transitions; no output clipping."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,kind='mlp'):
  super().__init__();self.kind=kind
  if kind=='mlp':
   self.net=nn.Sequential(nn.Linear(21,64),nn.SiLU(),nn.Linear(64,64),nn.SiLU(),nn.Linear(64,3));head=self.net[-1]
  else:
   assert kind=='gru';self.cell=nn.GRU(21,32,batch_first=True);self.head=nn.Linear(32,3);head=self.head
  nn.init.zeros_(head.weight);nn.init.zeros_(head.bias)
 def step(self,history,external,memory=None):
  x=torch.cat([history.flatten(1),external],-1)
  if self.kind=='gru':
   sequence,hidden=self.cell(x[:,None],None if memory is None else memory[None]);memory=hidden[0];delta=self.head(memory)
  else:delta=self.net(x)
  return history[:,-1]+delta*external[:,-1:],memory
 def forward(self,history,external):return self.step(history,external)[0]

def normalize_fit(raw,ids,config,scale):
 x=torch.asinh(raw/scale);means=[];seconds=[]
 for c in torch.unique(config[ids]):
  v=x[ids[config[ids]==c]];means.append(v.mean((0,1)));seconds.append(v.square().mean((0,1)))
 mean=torch.stack(means).mean(0);std=(torch.stack(seconds).mean(0)-mean.square()).clamp_min(0).sqrt().clamp_min(.05)
 return mean,std
