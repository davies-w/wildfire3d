"""Physical background-temperature penalty on a fixed dose/background baseline."""
from baseline_losses import objective_for as baseline
from previous_loss import quantities

def objective_for(arm,p,y,ambient):
 if arm=='control':return baseline('control',p,y,ambient)
 loss=baseline('dose_background',p,y,ambient)
 if arm in ['dose_background','dose_repeat']:return loss
 t,_,_=quantities(p);ty,_,_=quantities(y);mask=ty<=50;dims=(1,2,3);n=mask.sum(dims)
 values=((t-ty).abs()*mask).sum(dims)/n.clamp_min(1)/10
 physical=values[n>0].mean() if (n>0).any() else p.sum()*0
 return loss+({'physical_low':.02,'physical_high':.1}[arm])*physical
