"""Region-balanced encoded losses with stable strength and KL allocation."""
import torch
from torch.nn import functional as F
from previous_loss import quantities

def revised(p,y):
 t,q,g=quantities(p);ty,qy,gy=quantities(y);dims=(1,2,3)
 def region(v,m):
  n=m.sum(dims);return ((v*m).sum(dims)/n.clamp_min(1))[n>0].mean() if (n>0).any() else v.sum()*0
 hot=ty>50
 # Encoded squared errors strongly penalize missed fire, with per-frame normalization.
 temperature=region((p[:,0]-y[:,0]).square(),hot)+.1*region((p[:,0]-y[:,0]).square(),~hot)
 total=q.sum(dims)*.125;truth=qy.sum(dims)*.125
 strength=F.smooth_l1_loss(torch.log1p(total),torch.log1p(truth))
 alloc=q/q.sum(dims,keepdim=True).clamp_min(1e-12);target=qy/qy.sum(dims,keepdim=True).clamp_min(1e-12)
 kl=(target*(target.clamp_min(1e-12).log()-alloc.clamp_min(1e-12).log())).sum(dims);active=truth>1
 spatial=kl[active].mean() if active.any() else p.sum()*0
 bright=gy>5
 radiation=region((p[:,5]-y[:,5]).square(),bright)+.1*region((p[:,5]-y[:,5]).square(),~bright)
 velocity=(p[:,2:5]-y[:,2:5]).square().mean()
 temporal=(p[1:,:2]-p[:-1,:2]-(y[1:,:2]-y[:-1,:2])).square().mean() if len(p)>1 else p.sum()*0
 return temperature+.5*strength+.1*spatial+radiation+.2*velocity+.1*temporal
