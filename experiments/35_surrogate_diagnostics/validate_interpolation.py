"""Synthetic forward and derivative equivalence only, no training/optimization."""
from pathlib import Path
import json,torch
from torch.nn import functional as F
from deterministic_interpolation import double_trilinear

def validate(device='cpu'):
 torch.manual_seed(3311);rows=[]
 for shape in [(2,2,6,4,4),(1,2,12,8,8),(1,1,24,16,16)]:
  x=torch.randn(shape,device=device,requires_grad=True);y=x.detach().clone().requires_grad_(True)
  a=F.interpolate(x,scale_factor=2,mode='trilinear',align_corners=False);b=double_trilinear(y);v=torch.randn_like(a)
  da=torch.autograd.grad(a,x,v)[0];db=torch.autograd.grad(b,y,v)[0]
  f=float((a-b).abs().max().detach());g=float((da-db).abs().max());assert torch.allclose(a,b,atol=2e-6,rtol=2e-5);assert torch.allclose(da,db,atol=1e-5,rtol=2e-5)
  rows.append(dict(shape=shape,forward_max_abs=f,gradient_max_abs=g))
 p=Path(__file__).parent/'results/interpolation-check.json';p.write_text(json.dumps(dict(passed=True,device=device,scope='Synthetic operator and gradient checks, no training; CPU check does not establish CUDA determinism',rows=rows),indent=2))
 return rows
if __name__=='__main__':validate()
