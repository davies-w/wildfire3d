"""Matched loss ablation; radiation uses a short-window dose proxy."""
from losses import revised
from previous_loss import quantities

def objective_for(arm,p,y,ambient):
 base=revised(p,y)
 if arm=='control':return base
 _,_,g=quantities(p);ty,_,gy=quantities(y);dims=(1,2,3)
 def region(v,m):
  n=m.sum(dims);return ((v*m).sum(dims)/n.clamp_min(1))[n>0].mean() if (n>0).any() else v.sum()*0
 bright=gy>5
 old_rad=region((p[:,5]-y[:,5]).square(),bright)+.1*region((p[:,5]-y[:,5]).square(),~bright)
 pred=(g-ambient).clamp_min(0).sum(0);truth=(gy-ambient).clamp_min(0).sum(0)
 dose=(pred-truth).abs().mean()/(truth.mean()+1)
 loss=base-old_rad+.1*dose
 if arm=='dose_background':loss=loss+.4*region((p[:,0]-y[:,0]).square(),ty<=50)
 return loss
