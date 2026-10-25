"""Four observed states, three internal soft gates; no absorbing shutdown latch."""
import torch
from torch import nn
class Transition(nn.Module):
 def __init__(self,kind='control'):
  super().__init__();assert kind in ['control','gated'];self.kind=kind
  self.cell=nn.GRU(25,32,batch_first=True);self.head=nn.Linear(32,4);self.gate_head=nn.Linear(32,3)
  nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias);nn.init.zeros_(self.gate_head.weight);nn.init.constant_(self.gate_head.bias,4.)
  self.register_buffer('norm_mean',torch.zeros(4));self.register_buffer('norm_std',torch.ones(4));self.last_gate_logits=None
 def set_normalization(self,mean,std):
  self.norm_mean.copy_(mean);self.norm_std.copy_(std)
 def inputs(self,history,external):return torch.cat([history.flatten(1),external],-1)
 def step(self,history,external,memory=None):
  x=self.inputs(history,external);_,hidden=self.cell(x[:,None],None if memory is None else memory[None]);memory=hidden[0];delta=self.head(memory)*external[:,-1:];self.last_gate_logits=self.gate_head(memory);g=torch.sigmoid(self.last_gate_logits);candidate=history[:,-1]+delta
  if self.kind=='gated':
   masses=history[:,-1,:2]+g[:,:2]*delta[:,:2]
   # Physical gas release is suppressed, not frozen at the old nonzero rate.
   gas=torch.sinh(candidate[:,2]*self.norm_std[2]+self.norm_mean[2])*g[:,2]
   encoded=(torch.asinh(gas)-self.norm_mean[2])/self.norm_std[2]
   candidate=torch.cat([masses,encoded[:,None],candidate[:,3:4]],-1)
  return candidate,memory
 def forward(self,history,external):return self.step(history,external)[0]
def normalize_fit(raw,ids,config,scale):
 x=torch.asinh(raw/scale);means=[];seconds=[]
 for c in torch.unique(config[ids]):
  v=x[ids[config[ids]==c]];means.append(v.mean((0,1)));seconds.append(v.square().mean((0,1)))
 mean=torch.stack(means).mean(0);std=(torch.stack(seconds).mean(0)-mean.square()).clamp_min(0).sqrt().clamp_min(.05)
 return mean,std
