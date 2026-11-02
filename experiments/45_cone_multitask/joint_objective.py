"""Time-weighted cone losses, distinct from four-state physical integral."""
import torch
import torch.nn.functional as F
SCALES=(12.,90.,24.,16.,1500.)
def cone_terms(pred,logits,target,active,elapsed,beta=.1):
    # Mask by reference activity, never by predicted presence. NaNs are removed
    # before arithmetic, rather than multiplied by zero after contamination.
    target=torch.nan_to_num(target)
    scales=pred.new_tensor(SCALES)
    error=F.smooth_l1_loss(pred/scales,target/scales,reduction='none',beta=beta).mean(-1)
    weights=elapsed*active.to(elapsed.dtype)
    den=weights.sum(-1)
    parameter=(error*weights).sum(-1)/den.clamp_min(1e-12)
    presence=(F.binary_cross_entropy_with_logits(logits,active.to(logits.dtype),reduction='none')*elapsed).sum(-1)/elapsed.sum(-1)
    return parameter,presence
