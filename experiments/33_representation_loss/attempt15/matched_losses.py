"""Physical total heat-release error reduces absolute false burning in weak frames."""
from physical_background_losses import objective_for as baseline
from previous_loss import quantities

def strength_term(p,y):
 _,q,_=quantities(p);_,target,_=quantities(y)
 total=q.sum((1,2,3))*.125;truth=target.sum((1,2,3))*.125
 return ((total-truth).abs()/(truth+10)).mean()

def objective_for(arm,p,y,ambient):
 loss=baseline('physical_low',p,y,ambient)
 return loss+{'control':0.,'strength_low':.02,'strength_high':.1}[arm]*strength_term(p,y)
