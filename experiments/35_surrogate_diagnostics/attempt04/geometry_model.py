"""Height/loading-aware snapshot baseline; recurrent correction remains separate."""
import torch,numpy as np
from torch import nn
from torch.nn import functional as F
from original_cnn import CNN
class GeometryCNN(CNN):
 def __init__(self):
  super().__init__();self.fc[0]=nn.Linear(13,96)
 def warm_start(self,old):
  state=self.state_dict(); width=old['fc.0.weight'].shape[1]
  self.load_state_dict({k:v for k,v in old.items() if k in state and k!='fc.0.weight'},strict=False)
  with torch.no_grad():self.fc[0].weight[:,:width]=old['fc.0.weight'];self.fc[0].weight[:,width:]=0
 def forward(self,c):
  out=super().forward(c);raw=20+100*torch.sinh(out[:,:1].clamp(-5,5));te=torch.asinh((6+F.softplus(raw-6,beta=.5)-20)/100);return torch.cat([te,out[:,1:2].clamp(0,10),out[:,2:5],out[:,5:6].clamp(0,10)],1)
def features(g):
 # Sufficient descriptors for this narrow fixed-radius, same-shape height/loading experiment,
 # not a representation of arbitrary detailed tree architecture.
 q=g.sum(0);mass=q.sum()*.125;z=np.arange(32)*.5+.25;mean=(q*z[None,None,:]).sum()/q.sum();var=(q*(z[None,None,:]-mean)**2).sum()/q.sum();fol=g[0].sum()/max(g.sum(),1e-8)
 return np.array([np.log(max(mass,1e-6)/55.50214),(mean-4)/4,(var-3)/4,fol-.64],dtype=np.float32)
