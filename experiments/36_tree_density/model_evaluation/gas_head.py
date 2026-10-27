"""Bounded output-only gas calibration; frozen GRU dynamics are not corrected."""
import math
import torch
from torch import nn
class GasHead(nn.Module):
 def __init__(self,mean,std):
  super().__init__();assert mean.shape==std.shape==(46,)
  self.register_buffer('feature_mean',mean.clone());self.register_buffer('feature_std',std.clone())
  self.net=nn.Sequential(nn.Linear(46,16),nn.Tanh(),nn.Linear(16,1))
  nn.init.zeros_(self.net[-1].weight);nn.init.zeros_(self.net[-1].bias)
 def forward(self,features,base_gas):
  logfactor=math.log(2)*torch.tanh(self.net((features-self.feature_mean)/self.feature_std).squeeze(-1))
  return base_gas*torch.exp(logfactor)
