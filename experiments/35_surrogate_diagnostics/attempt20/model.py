"""Same-size GRUs, only thermal input/output enabled versus masked control."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,kind='control'):
  super().__init__();assert kind in ['control','thermal'];self.kind=kind;self.cell=nn.GRU(25,32,batch_first=True);self.head=nn.Linear(32,4);nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
 def inputs(self,history,external):
  if self.kind=='control':history=history*history.new_tensor([1,1,1,0])
  return torch.cat([history.flatten(1),external],-1)
 def step(self,history,external,memory=None):
  x=self.inputs(history,external);sequence,hidden=self.cell(x[:,None],None if memory is None else memory[None]);memory=hidden[0];state=history[:,-1]+self.head(memory)*external[:,-1:]
  if self.kind=='control':state=state*state.new_tensor([1,1,1,0])
  return state,memory
 def forward(self,history,external):return self.step(history,external)[0]

def normalize_fit(raw,ids,config,scale):
 x=torch.asinh(raw/scale);means=[];seconds=[]
 for c in torch.unique(config[ids]):
  v=x[ids[config[ids]==c]];means.append(v.mean((0,1)));seconds.append(v.square().mean((0,1)))
 mean=torch.stack(means).mean(0);std=(torch.stack(seconds).mean(0)-mean.square()).clamp_min(0).sqrt().clamp_min(.05)
 return mean,std
