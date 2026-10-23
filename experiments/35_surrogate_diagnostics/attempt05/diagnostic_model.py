"""Oracle conditioning preserves the exact baseline computation at initialization."""
import torch
from torch import nn
from geometry_model import GeometryCNN
class OracleCondition(nn.Module):
 def __init__(self,base):
  super().__init__();self.base=base;self.source=nn.Linear(1,96,bias=False);nn.init.zeros_(self.source.weight)
 def forward(self,x):return self.base(x[:,:13])+self.source(x[:,13:14])
class OracleCNN(GeometryCNN):
 def __init__(self,state):
  super().__init__();self.load_state_dict(state);self.fc[0]=OracleCondition(self.fc[0])
