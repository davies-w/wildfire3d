"""Remove only HRR clamp from encoded model outputs used by training."""
import torch
from torch.nn import functional as F
from geometry_model import GeometryCNN
from original_cnn import CNN
class RawHRRGeometryCNN(GeometryCNN):
 def forward(self,c):
  out=CNN.forward(self,c);raw=20+100*torch.sinh(out[:,:1].clamp(-5,5));te=torch.asinh((6+F.softplus(raw-6,beta=.5)-20)/100)
  return torch.cat([te,out[:,1:2],out[:,2:5],out[:,5:6].clamp(0,10)],1)
def common_encoded(p):return torch.cat([p[:,:1],p[:,1:2].clamp(0,10),p[:,2:]],1)
