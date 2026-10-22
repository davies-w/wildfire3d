"""Small shared spatial component model; no FDS access in forward/rollout.

64 nodes/tree: 16 spatial regions x four fuel classes. This pilot predicts
canopy states/heat transfer, not a full 3D gas/flame field. Static node features
come from geometry/templates. The heater is an explicit external input.
"""
import torch
from torch import nn
import torch.nn.functional as F

class ComponentGraph(nn.Module):
 def __init__(self):
  super().__init__()
  # Static features: four fuel-class indicators, radius, height, local xyz,
  # initial mass, area and occupied-region volume: 12 dimensions.
  self.response=nn.GRUCell(12+4,8)
  self.output=nn.Linear(8,3)
  # Sender-target displacement, distance, directional alignment; shared kernel.
  self.kernel=nn.Sequential(nn.Linear(5,12),nn.SiLU(),nn.Linear(12,2))
  self.local=nn.Sequential(nn.Linear(12+2,12),nn.SiLU(),nn.Linear(12,2))
  self.heater_gain=nn.Parameter(torch.zeros(2))

 def heat(self,static,xyz,instance,state,fuel_rate,heater_xyz,heater_strength,independent=False):
  delta=xyz[:,None,:]-xyz[None,:,:] # target minus source
  distance=torch.linalg.vector_norm(delta,dim=-1).clamp_min(.5)
  feat=torch.cat([delta/10,distance[...,None]/10,(delta[...,0]/distance)[...,None]],-1)
  kernel=F.softplus(self.kernel(feat))/(1+distance[...,None]**2)
  mask=~torch.eye(len(xyz),device=xyz.device,dtype=torch.bool)
  if independent:mask &= instance[:,None]==instance[None,:]
  kernel=kernel*mask[...,None]
  # Learned conversion of predicted fuel release to incoming radiation/convection.
  emitted=fuel_rate*17425. # kg/s * kJ/kg = kW
  incoming=(kernel*emitted[None,:,None]).sum(1)
  hd=xyz-heater_xyz;hr=torch.linalg.vector_norm(hd,dim=-1).clamp_min(.5)
  heater=heater_strength*F.softplus(self.heater_gain)[None,:]*100/(1+hr[:,None]**2)
  local=self.local(torch.cat([static,state],-1))
  radiation=.4187+F.softplus(local[:,0])*state[:,0]+incoming[:,0]+heater[:,0]
  convection=incoming[:,1]+heater[:,1]-F.softplus(local[:,1])*state[:,0]
  return torch.stack([radiation,convection],-1)

 def step(self,static,xyz,instance,state,hidden,fuel_rate,heater_xyz,heater_strength,dt=2.,independent=False,observed_heat=None):
  heat=self.heat(static,xyz,instance,state,fuel_rate,heater_xyz,heater_strength,independent)
  # observed_heat is ONLY for response-identification diagnostics/training;
  # autonomous rollout below never accepts it.
  forcing=heat if observed_heat is None else observed_heat
  hidden=self.response(torch.cat([static,state,forcing/100],-1),hidden)
  change=self.output(hidden)
  activity=(state[:,0].abs()+((forcing[:,0]-.4187).clamp_min(0)+forcing[:,1].clamp_min(0))/100).clamp(0,2)
  temp=(state[:,0]+dt*.25*torch.tanh(change[:,0])*activity).clamp(0,2.)
  # Thermal activation prevents unheated nodes consuming fuel spontaneously.
  loss_fraction=torch.minimum(state[:,1],dt*.01*F.softplus(change[:,1])*state[:,0].clamp_min(0)**2)
  fraction=state[:,1]-loss_fraction
  # Fuel-vapor release is only part of total wet/solid mass loss.
  rate=loss_fraction/dt*static[:,9].clamp_min(0)*torch.sigmoid(change[:,2])
  next_state=torch.stack([temp,fraction],-1)
  return next_state,hidden,rate,heat

 def rollout(self,static,xyz,instance,heater_xyz,schedule,dt=2.,independent=False):
  """Inputs are initial geometry/material descriptors and known heater schedule only."""
  n=len(xyz);state=torch.stack([torch.zeros(n,device=xyz.device),torch.ones(n,device=xyz.device)],-1)
  hidden=torch.zeros(n,8,device=xyz.device);rate=torch.zeros(n,device=xyz.device);states=[state];heats=[];rates=[]
  for strength in schedule:
   state,hidden,rate,heat=self.step(static,xyz,instance,state,hidden,rate,heater_xyz,strength,dt,independent)
   states.append(state);heats.append(heat);rates.append(rate)
  return torch.stack(states),torch.stack(heats),torch.stack(rates)

 def additive_rollout(self,static,xyz,instance,heater_xyz,schedule,dt=2.):
  # First predict each component independently. Then add its predicted emissions
  # through the same transport kernel, without allowing neighbours to change
  # those source-emission histories. Neither pass reads FDS outputs.
  _,_,isolated_rates=self.rollout(static,xyz,instance,heater_xyz,schedule,dt,independent=True)
  n=len(xyz);state=torch.stack([torch.zeros(n,device=xyz.device),torch.ones(n,device=xyz.device)],-1)
  hidden=torch.zeros(n,8,device=xyz.device);states=[state];heats=[];rates=[]
  for j,strength in enumerate(schedule):
   imposed=torch.zeros(n,device=xyz.device) if j==0 else isolated_rates[j-1]
   state,hidden,rate,heat=self.step(static,xyz,instance,state,hidden,imposed,heater_xyz,strength,dt,False)
   states.append(state);heats.append(heat);rates.append(rate)
  return torch.stack(states),torch.stack(heats),torch.stack(rates)

if __name__=='__main__':
 torch.manual_seed(26);m=ComponentGraph();n=128
 static=torch.zeros(n,12);static[:,9]=.1;xyz=torch.randn(n,3);instance=torch.arange(n)//64
 out=m.rollout(static,xyz,instance,torch.tensor([0.,0.,2.1]),[1.]*10+[0.]*5)
 assert all(torch.isfinite(v).all() for v in out)
 loss=sum(v.square().mean() for v in out);loss.backward();assert all(p.grad is not None for p in m.parameters())
 cold=m.rollout(static,xyz,instance,torch.tensor([0.,0.,2.1]),[0.]*15)
 assert torch.max(torch.abs(cold[0][:,:,0]))==0 and torch.max(torch.abs(cold[0][:,:,1]-1))==0 and torch.max(cold[2])==0
 print('Untrained architecture smoke check:',sum(p.numel() for p in m.parameters()),'parameters; output shapes',[tuple(v.shape) for v in out])
