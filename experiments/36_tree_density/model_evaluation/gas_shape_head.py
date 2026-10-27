"""Full-forecast gas shape correction with preserved positive/negative integrals."""
import math
import torch
from torch import nn
class GasShapeHead(nn.Module):
 def __init__(self,mean,std):
  super().__init__();assert mean.shape==std.shape==(46,)
  self.register_buffer('feature_mean',mean.clone());self.register_buffer('feature_std',std.clone());self.net=nn.Sequential(nn.Linear(46,16),nn.Tanh(),nn.Linear(16,1));nn.init.zeros_(self.net[-1].weight);nn.init.zeros_(self.net[-1].bias)
 def forward(self,features,base_gas,times):
  assert features.shape[:2]==base_gas.shape and times.shape==(base_gas.shape[0],base_gas.shape[1]+1)
  dt=times[:,1:]-times[:,:-1];assert bool((dt>0).all());quadrature=.5*dt;quadrature=torch.cat([quadrature[:,:-1]+.5*dt[:,1:],quadrature[:,-1:]],1)
  factor=torch.exp((math.log(2)/2)*torch.tanh(self.net((features-self.feature_mean)/self.feature_std).squeeze(-1)))
  def average(amount):
   amount=amount*quadrature;den=amount.sum(1,keepdim=True);value=(amount*factor).sum(1,keepdim=True)/den.clamp_min(torch.finfo(amount.dtype).tiny);return torch.where(den>0,value,torch.ones_like(value))
  normalizer=torch.where(base_gas>=0,average(base_gas.clamp_min(0)),average((-base_gas).clamp_min(0)))
  return base_gas*factor/normalizer
