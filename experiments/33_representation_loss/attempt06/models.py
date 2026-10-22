import torch
from torch import nn
from torch.nn import functional as F
class SpatialHeads(nn.Module):
 """Full .5m density/source inputs; shared encoder with independent output decoders."""
 def __init__(self):
  super().__init__()
  def block(a,b):return nn.Sequential(nn.Conv3d(a,b,3,padding=1),nn.SiLU(),nn.Conv3d(b,b,3,padding=1),nn.SiLU())
  self.e0=block(21,12);self.e1=block(12,24);self.e2=block(24,32)
  self.heads=nn.ModuleDict({n:nn.ModuleList([block(56,24),block(36,12),nn.Conv3d(12,k,1)]) for n,k in [('temperature',1),('combustion',1),('radiation',1),('airflow',3)]})
  self.strength=nn.Sequential(nn.Linear(45,48),nn.SiLU(),nn.Linear(48,1))
  self.register_buffer('coords',torch.stack(torch.meshgrid(torch.linspace(0,1,48),torch.linspace(0,1,32),torch.linspace(0,1,32),indexing='ij'))[None])
  for name,head in self.heads.items():nn.init.zeros_(head[-1].weight);nn.init.zeros_(head[-1].bias)
  nn.init.zeros_(self.strength[-1].weight);nn.init.constant_(self.strength[-1].bias,0.)
 def forward(self,c,g,source):
  b=c.shape[0];shape=g.shape[2:];x=torch.cat([g/10,source,self.coords.expand(b,-1,-1,-1,-1),c[:,:,None,None,None].expand(-1,-1,*shape)],1)
  e0=self.e0(x);e1=self.e1(F.avg_pool3d(e0,2));e2=self.e2(F.avg_pool3d(e1,2));out={}
  for name,head in self.heads.items():
   y=head[0](torch.cat([F.interpolate(e2,size=e1.shape[2:],mode='trilinear',align_corners=False),e1],1));y=head[1](torch.cat([F.interpolate(y,size=shape,mode='trilinear',align_corners=False),e0],1));out[name]=head[2](y)
  strength=torch.exp(self.strength(torch.cat([e2.mean((2,3,4)),c],1)).clamp(-20,15))
  allocation=out['combustion'].flatten(1).softmax(1).reshape(b,1,*shape);q=allocation*strength[:,:,None,None,None]/.125
  raw=20+100*torch.sinh(out['temperature'].clamp(-5,5));te=torch.asinh((6+F.softplus(raw-6,beta=.5)-20)/100)
  # Radiation is positive absolute integrated intensity; initialize near ambient.
  radiation=torch.exp(out['radiation'].clamp(-20,15))*1.67506325
  return torch.cat([te,torch.log1p(q/10),out['airflow'],torch.log1p(radiation/2)],1)
