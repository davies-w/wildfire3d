"""Autonomous 2-second field/material transition. No reference fields at inference."""
import numpy as np,torch,math
from torch import nn
from torch.nn import functional as F
from original_cnn import encode,decode
class Sequence(nn.Module):
 def __init__(self,geometry):
  super().__init__();g=torch.as_tensor(geometry,dtype=torch.float32)[None];self.register_buffer('geometry',g);self.register_buffer('initial_mass',F.avg_pool3d(g,4)*8)
  self.register_buffer('normalized_geometry',g/10.);xx=torch.meshgrid(torch.linspace(0,1,48),torch.linspace(0,1,32),torch.linspace(0,1,32),indexing='ij');self.register_buffer('coords',torch.stack(xx)[None])
  self.enc=nn.Sequential(nn.Conv3d(24,16,3,stride=2,padding=1),nn.SiLU(),nn.Conv3d(16,24,3,stride=2,padding=1),nn.SiLU())
  self.gates=nn.Conv3d(48,48,3,padding=1);self.candidate=nn.Conv3d(48,24,3,padding=1)
  self.dec1=nn.Conv3d(24,16,3,padding=1);self.dec2=nn.Conv3d(16,8,3,padding=1);self.out=nn.Conv3d(8,6,3,padding=1);self.material=nn.Conv3d(24,8,3,padding=1)
  nn.init.zeros_(self.out.weight);nn.init.zeros_(self.out.bias);self.out.bias.data[1]=.01
  nn.init.zeros_(self.material.weight);nn.init.zeros_(self.material.bias);self.material.bias.data[:4]=-4
 def set_geometry(self,geometry):
  g=torch.as_tensor(geometry,dtype=torch.float32,device=self.geometry.device)[None];self.geometry=g;self.initial_mass=F.avg_pool3d(g,4)*8;self.normalized_geometry=g/10.
 def initialize(self,c):
  d=self.geometry.device; a=np.zeros((1,6,48,32,32),np.float32);a[:,0]=20;a[:,2]=c['wind_speed'];a[:,5]=1.6750632524490356
  p=torch.from_numpy(encode(a,c['wind_speed'])).to(d);m=(self.initial_mass>0).float();temp=torch.zeros_like(m);return p,m,temp,None
 def source(self,c):
  a=np.zeros((48,32,32),np.float32);angles=np.deg2rad(c['angle_deg']-30+60*(np.arange(1600)+.5)/1600);ix=np.array([(8+1.2*np.cos(angles))/.5,(8+1.2*np.sin(angles))/.5,np.full(1600,2.1/.5)]).astype(int);np.add.at(a,tuple(ix),1);a/=max(a.max(),1);return torch.from_numpy(a)[None,None].to(self.geometry.device)
 def forward(self,p,m,temp,h,c,t,source,baseline=None):
  shape=p.shape[2:];b=p.shape[0];src=source*float(t<20.1);mass=F.interpolate(m,size=shape,mode='nearest');tp=F.interpolate(temp,size=shape,mode='nearest');wind=torch.full_like(src,c['wind_speed']/5);moist=torch.full_like(src,c['moisture'])
  x=torch.cat([p,self.normalized_geometry.expand(b,-1,-1,-1,-1),src,self.coords.expand(b,-1,-1,-1,-1),wind,moist,mass,tp],1);x=self.enc(x)
  if h is None:h=torch.zeros_like(x)
  z,r=torch.sigmoid(self.gates(torch.cat([x,h],1))).chunk(2,1);candidate=torch.tanh(self.candidate(torch.cat([x,r*h],1)));h=(1-z)*h+z*candidate
  y=F.silu(self.dec1(F.interpolate(h,scale_factor=2,mode='trilinear',align_corners=False)));y=F.silu(self.dec2(F.interpolate(y,scale_factor=2,mode='trilinear',align_corners=False)));out=p+.25*self.out(y) if baseline is None else baseline+.5*torch.tanh(self.out(y))
  rawT=20+100*torch.sinh(out[:,:1].clamp(-5,5));te=torch.asinh(((6+F.softplus(rawT-6,beta=.5) if baseline is None else rawT.clamp_min(6))-20)/100);out=torch.cat([te,out[:,1:2].clamp(0,10),out[:,2:5].clamp(-10,10),out[:,5:6].clamp(0,10)],1)
  mat=self.material(h);m=m*torch.exp(-.1*F.softplus(mat[:,:4]));temp=(temp+.1*mat[:,4:]).clamp(-.14,4)
  return out,m,temp,h
 @torch.no_grad()
 def rollout(self,c,times,reset_memory=False):
  p,m,temp,h=self.initialize(c);src=self.source(c);fields=[decode(p.cpu().numpy(),c['wind_speed'])[0]];masses=[(m*self.initial_mass).cpu().numpy()[0]]
  for t in times[:-1]:
   p,m,temp,h=self(p,m,temp,None if reset_memory else h,c,float(t),src);fields.append(decode(p.cpu().numpy(),c['wind_speed'])[0]);masses.append((m*self.initial_mass).cpu().numpy()[0])
  return np.stack(fields),np.stack(masses)
