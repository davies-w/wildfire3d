"""Separable align_corners=False factor-two linear interpolation using matrix products.
Same real-arithmetic rule as trilinear interpolation; floating-point order differs.
Dense matrices avoid CUDA interpolation's atomic accumulation in backward.
"""
import torch
_CACHE={}
def weights(n,device,dtype):
 key=(n,str(device),dtype)
 if key not in _CACHE:
  pos=(torch.arange(2*n,device=device,dtype=dtype)+.5)/2-.5
  low=pos.floor();f=pos-low;low=low.long();high=low+1
  j=torch.arange(n,device=device)
  _CACHE[key]=((j[None,:]==low.clamp(0,n-1)[:,None])*(1-f[:,None])+(j[None,:]==high.clamp(0,n-1)[:,None])*f[:,None]).to(dtype)
 return _CACHE[key]
def double_trilinear(x):
 for axis in [-1,-2,-3]:
  w=weights(x.shape[axis],x.device,x.dtype)
  x=torch.matmul(x.movedim(axis,-1),w.T).movedim(-1,axis)
 return x
