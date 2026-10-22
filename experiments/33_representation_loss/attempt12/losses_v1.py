import torch
from torch.nn import functional as F
from previous_loss import quantities

def revised(p,y):
 t,q,g=quantities(p);ty,qy,gy=quantities(y);dims=(1,2,3);hot=ty>50
 def region(v,mask):return (v*mask).sum()/mask.sum().clamp_min(1)
 temperature=region((t-ty).abs()/100,hot)+region((t-ty).abs()/10,~hot)
 total=q.sum(dims)*.125;truth=qy.sum(dims)*.125
 strength=((torch.log1p(total)-torch.log1p(truth)).abs()+abs(total-truth)/truth.clamp_min(1)).mean()
 # Compare allocation only when reference combustion is appreciable.
 alloc=q/(q.sum(dims,keepdim=True).clamp_min(1e-6));target=qy/qy.sum(dims,keepdim=True).clamp_min(1e-6)
 mask=truth>1;spatial=((alloc-target).abs().sum(dims)*mask).sum()/mask.sum().clamp_min(1)
 multi=0.
 for k in [2,4]:multi=multi+(F.avg_pool3d(p[:,:2],k)-F.avg_pool3d(y[:,:2],k)).abs().mean()
 radiation=((g-gy).abs().mean(dims)/(gy.mean(dims)+1)).mean()
 velocity=(p[:,2:5]-y[:,2:5]).abs().mean()
 # Consecutive frames: penalize incorrect changes without prescribing smoothness.
 temporal=(p[1:,:2]-p[:-1,:2]-(y[1:,:2]-y[:-1,:2])).abs().mean() if len(p)>1 else p.sum()*0
 return temperature+.25*strength+.25*spatial+.25*multi+.25*radiation+velocity+.2*temporal
