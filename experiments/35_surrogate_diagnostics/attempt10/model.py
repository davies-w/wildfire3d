"""Attempt07 U-Net blocks; 14 inputs (13 static + time), six raw encoded outputs."""
import torch
from torch import nn
class Block(nn.Sequential):
 def __init__(self,a,b):
  super().__init__(nn.Conv3d(a,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU(),nn.Conv3d(b,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU())
class FieldUNet(nn.Module):
 def __init__(self):
  super().__init__();self.enc=nn.ModuleList([Block(14,8),Block(16,16),Block(32,32),Block(64,64)]);self.down=nn.ModuleList([nn.Conv3d(8,16,2,stride=2),nn.Conv3d(16,32,2,stride=2),nn.Conv3d(32,64,2,stride=2)]);self.dec=nn.ModuleList([Block(96,32),Block(48,16),Block(24,8)]);self.out=nn.Conv3d(8,6,1)
 def forward(self,x):
  skips=[]
  for i in range(3):x=self.enc[i](x);skips.append(x);x=self.down[i](x)
  x=self.enc[3](x)
  for layer,s in zip(self.dec,reversed(skips)):
   for axis in [2,3,4]:x=x.repeat_interleave(2,dim=axis)
   x=layer(torch.cat([x,s],1))
  return self.out(x)
def encode(a,w):
 b=a.clone();b[:,0]=torch.asinh((a[:,0]-20)/100);b[:,1]=torch.log1p(a[:,1].clamp_min(0)/10);b[:,2]=(a[:,2]-w)/5;b[:,3:5]=a[:,3:5]/5;b[:,5]=torch.log1p(a[:,5].clamp_min(0)/2);return b

def physical(p,w):
 # Bounds apply only to reported physical predictions, NEVER to training outputs.
 return torch.stack([20+100*torch.sinh(p[:,0].clamp(-5,5)),10*torch.expm1(p[:,1].clamp(0,10)),5*p[:,2]+w,5*p[:,3],5*p[:,4],2*torch.expm1(p[:,5].clamp(0,10))],1)

def channel_losses(p,y,scales):
 e=((p-y)/scales[None,:,None,None,None]).square();whole=e.mean((2,3,4));terms=[]
 for j,threshold in [(0,0.2956730476),(1,0.0009995003331)]:
  mask=y[:,j]>threshold;count=mask.sum((1,2,3));n=mask[0].numel();active=(e[:,j]*mask).sum((1,2,3))/count.clamp_min(1);cold=(e[:,j]*(~mask)).sum((1,2,3))/(n-count).clamp_min(1)
  terms.append(torch.where((count>0)&(count<n),.5*(active+cold),whole[:,j]))
 return torch.stack([*terms,*whole[:,2:].unbind(1)],1),whole
