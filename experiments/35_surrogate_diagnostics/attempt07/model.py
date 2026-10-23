"""Fixed spatial U-Net. NO time input; each time has independent model/optimizer."""
import torch
from torch import nn
class Block(nn.Sequential):
 def __init__(self,a,b):
  super().__init__(nn.Conv3d(a,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU(),nn.Conv3d(b,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU())
class HotUNet(nn.Module):
 def __init__(self):
  super().__init__();self.enc=nn.ModuleList([Block(13,8),Block(16,16),Block(32,32),Block(64,64)]);self.down=nn.ModuleList([nn.Conv3d(8,16,2,stride=2),nn.Conv3d(16,32,2,stride=2),nn.Conv3d(32,64,2,stride=2)]);self.dec=nn.ModuleList([Block(96,32),Block(48,16),Block(24,8)]);self.out=nn.Conv3d(8,1,1)
 def forward(self,x):
  skips=[]
  for i in range(3):x=self.enc[i](x);skips.append(x);x=self.down[i](x)
  x=self.enc[3](x)
  for layer,s in zip(self.dec,reversed(skips)):
   for axis in [2,3,4]:x=x.repeat_interleave(2,dim=axis)
   x=layer(torch.cat([x,s],1))
  return self.out(x)[:,0]

def metrics(v):
 tp,fp,fn,tn=[float(x) for x in v[:4]]
 def div(a,b):return a/b if b else None
 return dict(precision=div(tp,tp+fp),recall=div(tp,tp+fn),f1=div(2*tp,2*tp+fp+fn),iou=div(tp,tp+fp+fn),false_positive_rate=div(fp,fp+tn),hot_fraction=div(tp+fn,tp+fp+fn+tn),predicted_hot_fraction=div(tp+fp,tp+fp+fn+tn),tp=tp,fp=fp,fn=fn,tn=tn)
