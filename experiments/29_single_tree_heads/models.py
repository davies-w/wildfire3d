"""Time-conditioned candidates, no sequential state and no FDS inference inputs."""
import json
import torch
from torch import nn
from torch.nn import functional as F
from original_cnn import CNN,ROOT
class Strength(nn.Module):
 def __init__(self):
  super().__init__();self.register_buffer('centers',torch.linspace(0,1,25));self.net=nn.Sequential(nn.Linear(33,64),nn.SiLU(),nn.Linear(64,64),nn.SiLU(),nn.Linear(64,1))
 def forward(self,c):
  basis=torch.exp(-((c[:,3:4]-self.centers)/.055).square());return F.softplus(self.net(torch.cat([c,basis],1))[:,0])
class Model(CNN):
 def __init__(self,kind='bounded',floor=0.):
  super().__init__();self.kind=kind;self.register_buffer('floor_C',torch.tensor(float(floor)))
  if kind=='heads':
   self.heads=nn.ModuleList([nn.Sequential(nn.Conv3d(8,8,3,padding=1),nn.SiLU(),nn.Conv3d(8,n,3,padding=1)) for n in [1,1,3,1]])
   # Residual branches start at zero; original output acts as warm-start skip.
   for h in self.heads:nn.init.zeros_(h[-1].weight);nn.init.zeros_(h[-1].bias)
   self.strength=Strength()
 def forward(self,c):
  x=self.fc(c).reshape(-1,16,6,4,4)
  for layer in self.layers:x=F.silu(layer(F.interpolate(x,scale_factor=2,mode='trilinear',align_corners=False)))
  p=self.out(x)
  if self.kind=='heads':p=p+torch.cat([h(x) for h in self.heads],1)
  # Smooth lower bound on an ambient-relative gas-temperature prediction.
  rawT=20+100*torch.sinh(p[:,0:1].clamp(-5,5));temp=self.floor_C+F.softplus(rawT-self.floor_C,beta=.5);te=torch.asinh((temp-20)/100)
  q=p[:,1:2]
  if self.kind=='heads':
   shape=10*torch.expm1(q.clamp(0,10))+1e-12
   total=torch.expm1(self.strength(c).clamp(0,18)).reshape(-1,1,1,1,1)
   physical_q=shape/(shape.sum((2,3,4),keepdim=True)*.125)*total
   q=torch.log1p(physical_q/10)
  return torch.cat([te,q,p[:,2:]],1)
def make(kind):
 floor=json.loads((ROOT/'results/temperature-bound.json').read_text())['floor_C'];m=Model(kind,floor);m.load_state_dict(torch.load(ROOT/'data/models/previous.pt',map_location='cpu',weights_only=True),strict=False)
 if kind=='heads':
  m.strength.load_state_dict(torch.load(ROOT/'data/models/strength.pt',map_location='cpu',weights_only=True))
  for p in m.strength.parameters():p.requires_grad_(False)
 return m
