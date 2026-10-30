"""Physical-space absolute piecewise-linear error integral, normalized by truth range."""
import torch
def interval_error(left,right):
    a,b=left.abs(),right.abs();cross=left*right<0
    # Safe inactive branch prevents 0/0 gradients at exact agreement.
    divisor=torch.where(a+b>0,2*(a+b),torch.ones_like(a))
    return torch.where(cross,(a.square()+b.square())/divisor,(a+b)/2)
def sequence_score(pred,truth,times,ranges):
    assert bool((ranges>0).all()),'Zero-range reference requires explicit policy; no silent floor'
    delta=pred-truth;areas=interval_error(delta[:,:-1],delta[:,1:])*(times[:,1:]-times[:,:-1])[:,:,None]
    return areas.sum(1)/((times[:,-1]-times[:,0])[:,None]*ranges)
