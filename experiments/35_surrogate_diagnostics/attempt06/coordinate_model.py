"""Explicit normalized x,y,z,t with fixed Fourier features; no learned spatial decoder."""
import torch
from torch import nn
class CoordinateMLP(nn.Module):
 def __init__(self):
  super().__init__();self.net=nn.Sequential(nn.Linear(52,128),nn.SiLU(),nn.Linear(128,128),nn.SiLU(),nn.Linear(128,128),nn.SiLU(),nn.Linear(128,6))
 def forward(self,x):
  z=x[:,:,None]*(2.**torch.arange(6,device=x.device))*torch.pi
  return self.net(torch.cat([x,z.sin().flatten(1),z.cos().flatten(1)],1))
def physical(p,wind):
 return torch.stack([20+100*torch.sinh(p[:,0].clamp(-5,5)),10*torch.expm1(p[:,1].clamp(0,10)),5*p[:,2]+wind,5*p[:,3],5*p[:,4],2*torch.expm1(p[:,5].clamp(0,10))],1)
