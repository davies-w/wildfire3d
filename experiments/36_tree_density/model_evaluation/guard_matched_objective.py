"""Match quiet training pressure to configuration-weighted aggregate quiet guards.

The linear delta estimates are unbiased under the fixed50/50full/rolling draw.
The nonlinear minibatch penalty is not an unbiased loss or an acceptance guarantee.
Quiet counts/weights use fit targets only and never enter forecast inputs.
"""
import torch
from context_objective import objective as pointwise_objective

def quiet_aggregate_penalty(prediction,truth,base,labels,full,valid_mask,scales,quiet_count,quiet_replica_weight,quiet_normalization):
    gap=(prediction-truth).abs()-(base-truth).abs();quiet=valid_mask&(labels==0);den=quiet_count.clamp_min(1)[:,None]
    all_quiet=(gap*quiet[:,:,None]).sum(1)/den
    early_quiet=(gap[:,:15]*quiet[:,:15,None]).sum(1)/den
    endpoint=gap[:,15]*quiet[:,15,None]/den
    zero=torch.zeros_like(all_quiet)
    auto=torch.where(full[:,None],2*all_quiet,zero)
    display=torch.where(full[:,None],2*early_quiet,150*endpoint)
    estimate=lambda value:quiet_normalization*(value*quiet_replica_weight[:,None]).mean(0)
    estimates=dict(autonomous=estimate(auto),display=estimate(display));slack=.001*scales
    penalty=lambda value:torch.log1p((value-slack).clamp_min(0)/slack).mean()
    return .5*(penalty(estimates['autonomous'])+penalty(estimates['display'])),estimates

def objective(prediction,truth,initial,times,scales,std,state_weights,replica_weights,full_history_gas_peak,valid_mask,*,base,labels,full,normalization,quiet_count,quiet_replica_weight,quiet_normalization):
    _,parts=pointwise_objective(prediction,truth,initial,times,scales,std,state_weights,replica_weights,full_history_gas_peak,valid_mask,base=base,labels=labels,full=full,normalization=normalization)
    quiet,_=quiet_aggregate_penalty(prediction,truth,base,labels,full,valid_mask,scales,quiet_count,quiet_replica_weight,quiet_normalization)
    # Reconstruct unchanged terms directly; do not subtract two rounded total losses.
    loss=parts['physical']+.25*parts['encoded_nonharm']+quiet+.1*parts['under_tail']+.05*parts['over_tail']+.05*parts['peak_error']+.1*parts['sampling_residual_error']
    return loss,{**parts,'quiet_nonharm':quiet}
