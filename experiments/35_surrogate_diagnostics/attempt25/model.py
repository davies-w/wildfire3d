"""Plain four-state GRU with no gates or physical constraints."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,kind='control'):
  super().__init__();assert kind=='control';self.kind=kind
  self.cell=nn.GRU(25,32,batch_first=True);self.head=nn.Linear(32,4)
  nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
  self.register_buffer('norm_mean',torch.zeros(4));self.register_buffer('norm_std',torch.ones(4))
 def set_normalization(self,mean,std):
  self.norm_mean.copy_(mean);self.norm_std.copy_(std)
 def inputs(self,history,external):return torch.cat([history.flatten(1),external],-1)
 def step(self,history,external,memory=None):
  x=self.inputs(history,external);_,hidden=self.cell(x[:,None],None if memory is None else memory[None]);memory=hidden[0];delta=self.head(memory)*external[:,-1:];candidate=history[:,-1]+delta
  return candidate,memory
 def forward(self,history,external):return self.step(history,external)[0]
def normalize_fit(raw,ids,config,scale):
 x=torch.asinh(raw/scale);means=[];seconds=[]
 for c in torch.unique(config[ids]):
  v=x[ids[config[ids]==c]];means.append(v.mean((0,1)));seconds.append(v.square().mean((0,1)))
 mean=torch.stack(means).mean(0);std=(torch.stack(seconds).mean(0)-mean.square()).clamp_min(0).sqrt().clamp_min(.05)
 return mean,std
