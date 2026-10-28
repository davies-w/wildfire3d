"""Physical-error objective aligned with scored forecast regimes and quiet labels.

Nonharm terms are soft training penalties, not guarantees of acceptance. Quiet
penalty is deliberately pointwise, stronger than the aggregate reported guard.
"""
import torch
from joint_objective_v2 import objective as encoded_objective

def objective(prediction,truth,initial,times,scales,std,state_weights,replica_weights,
              full_history_gas_peak,valid_mask,*,base,labels,full,normalization):
    _,old=encoded_objective(prediction,truth,initial,times,scales,std,state_weights,replica_weights,full_history_gas_peak,valid_mask)
    error=(prediction-truth).abs();base_error=(base-truth).abs();dtype=prediction.dtype;device=prediction.device
    norm=lambda key:torch.as_tensor(normalization[key],device=device,dtype=dtype).clamp_min(1e-8)
    # With50%full /50%rolling sampling, expected weights are25%autonomous
    # and75%exact display(first15full targets plus75rolling endpoints).
    full_loss=.5*(error.mean(1)/norm('autonomous_MAE')).mean(1)+.25*(error[:,:15].mean(1)/norm('display_MAE')).mean(1)
    rolling_loss=1.25*(error[:,15]/norm('display_MAE')).mean(1)
    per_case=torch.where(full,full_loss,rolling_loss)
    physical=(per_case*replica_weights).sum()/replica_weights.sum()
    positions=torch.arange(prediction.shape[1],device=device)[None]
    scored=torch.where(full[:,None],valid_mask,valid_mask&(positions==15))
    quiet=scored&(labels==0);count=quiet.sum(1);eligible=count>0
    # Allowed per-point slack matches the scale of the aggregate guard, but
    # pointwise no-harm is stricter and may reject useful compensating changes.
    excess=((error-base_error-.001*scales).clamp_min(0)/(.001*scales))
    qcase=(torch.log1p(excess).mean(-1)*quiet).sum(1)/count.clamp_min(1)
    quiet_loss=(qcase[eligible]*replica_weights[eligible]).sum()/replica_weights[eligible].sum() if bool(eligible.any()) else prediction.sum()*0
    encoded=((torch.asinh(prediction/scales)-torch.asinh(truth/scales))/std).square()[:,:,:3]
    old_encoded=((torch.asinh(base/scales)-torch.asinh(truth/scales))/std).square()[:,:,:3]
    deterioration=(encoded-old_encoded).clamp_min(0).mean(-1)
    ecase=(deterioration*scored).sum(1)/scored.sum(1).clamp_min(1)
    enorm=torch.where(full,norm('autonomous_objective'),norm('display_objective'))
    encoded_nonharm=((ecase/enorm)*replica_weights).sum()/replica_weights.sum()
    loss=physical+.25*encoded_nonharm+quiet_loss+.1*old['under_tail']+.05*old['over_tail']+.05*old['peak_error']+.1*old['sampling_residual_error']
    return loss,dict(physical=physical,quiet_nonharm=quiet_loss,encoded_nonharm=encoded_nonharm,**{k:v for k,v in old.items() if k!='state'})
