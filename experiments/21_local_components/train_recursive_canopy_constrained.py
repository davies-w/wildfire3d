"""Train shared canopy transitions by differentiating90s recursive trajectories.
During training, neighbouring building states are measured boundary conditions.
Validation/inference remains fully autonomous; this training simplification is explicit.
"""
import json,time
import numpy as np
import torch
from torch import nn
from scene import ROOT
import component_hot_state_model as hot
import component_heat_rule as exchange
torch.set_num_threads(2);torch.manual_seed(431)
TRAIN=['b21_single_1','b21_single_2','b21_transfer_0','b21_transfer_hot','b21_combined_0','b21_corner_1','b21_combined_1']
cases=[hot.series(json.loads((ROOT/'data/component_states'/f'{n}.json').read_text())) for n in TRAIN]
base=exchange.fit({},cases)
class Rule(nn.Module):
 def __init__(self):
  super().__init__();self.a=nn.Linear(14,12);self.b=nn.Linear(12,6,bias=False);nn.init.normal_(self.b.weight,0,.01)
 def forward(self,x):return self.b(torch.tanh(self.a(x)))-self.b(torch.tanh(self.a(torch.zeros_like(x))))
rule=Rule();opt=torch.optim.Adam(rule.parameters(),lr=.003)
scale=torch.tensor([500.,1500.,1.,300.,1.,1.]);origin=torch.tensor([20.,20.,1.,0.,0.,0.])
def norm(s):return torch.stack([(s[:,0]-20)/500,(s[:,1]-20)/1500,1-s[:,2],torch.sqrt(torch.clamp(s[:,3],min=0))/300,s[:,4],s[:,5]],1)
def decode(z):return torch.stack([20+500*z[:,0],20+1500*z[:,1],1-z[:,2],90000*z[:,3]**2,z[:,4],z[:,5]],1)
prepared=[]
for c in cases:
 g=c['g'];v=np.array([n['kind']=='vegetation' for n in g['nodes']]);prepared.append(dict(g=g,v=torch.tensor(v),truth=torch.tensor(c['state'],dtype=torch.float32),kernel=torch.tensor(g['kernel'],dtype=torch.float32),align=torch.tensor(g['aligned'],dtype=torch.float32),area=torch.tensor([n['area'] for n in g['nodes']],dtype=torch.float32),src=torch.tensor(g['source_kernel'],dtype=torch.float32),target=torch.stack([norm(torch.tensor(s[v],dtype=torch.float32)) for s in c['state']])))
def heat(d,s,t):
 e=torch.clamp(s[:,3],min=0);msg=d['kernel']*(e*d['area'])[None,:];pulse=min(t/.1,1) if t<=20 else max(0,1-(t-20)/.1)
 x=torch.stack([msg.sum(1)/100,(msg*d['align']).sum(1)*d['g']['wind_speed']/400,d['src']*12*pulse,e/1000,(s[:,0]-20)/500],1);coef=base['exchange_heads']['vegetation'];return torch.stack([x[:,:4]@torch.tensor(coef[0],dtype=torch.float32),x@torch.tensor(coef[1],dtype=torch.float32)],1)
def feat(d,s,h,t):
 pulse=min(t/.1,1) if t<=20 else max(0,1-(t-20)/.1);src=d['src']*pulse;active=(s[:,0]-20)/500
 return torch.stack([active,(s[:,1]-20)/1500,s[:,2]-1,torch.sqrt(torch.clamp(s[:,3],min=1e-10))/300,s[:,4],s[:,5],torch.asinh(h[:,0]/10),torch.asinh(h[:,1]/10),src,src*d['g']['wind_speed']/4,src*d['g']['moisture'],active*d['g']['moisture'],s[:,4]*s[:,2],s[:,5]*s[:,2]],1)
folder=ROOT/'data/recursive_canopy_constrained';folder.mkdir(exist_ok=True);history=[];start=time.time()
for epoch in range(1,301):
 opt.zero_grad();total=0
 for d in prepared:
  z=torch.zeros_like(d['target'][0]);loss=0
  for k in range(len(d['truth'])-1):
   s=d['truth'][k].clone();s[d['v']]=decode(z);h=heat(d,s,k*.5);x=feat(d,s,h,k*.5)[d['v']]
   proposed=z+.5*rule(x)
   bounded=torch.minimum(torch.clamp(proposed,min=0),torch.tensor([5.,1.65,1.,3.,1.,1.]))
   # Monotone consumed fuel and ordered hot fractions are part of training.
   consumed=torch.maximum(z[:,2],bounded[:,2]);hot300=bounded[:,4];hot500=torch.minimum(hot300,bounded[:,5])
   bounded=torch.stack([bounded[:,0],torch.maximum(bounded[:,1],bounded[:,0]/3),consumed,bounded[:,3],hot300,hot500],1)
   z=bounded
   loss=loss+((z-d['target'][k+1])**2*torch.tensor([1.,1.,1.,2.,1.,1.])).mean()
  loss=loss/(len(d['truth'])-1);loss.backward();total+=float(loss.detach())
 torch.nn.utils.clip_grad_norm_(rule.parameters(),5);opt.step();history.append(dict(epoch=epoch,loss=total/len(prepared)))
 if epoch%25==0:
  payload=dict(training_cases=TRAIN,epoch=epoch,loss=history[-1]['loss'],weights={k:v.detach().numpy().tolist() for k,v in rule.state_dict().items()},exchange_heads=base['exchange_heads'],scope='Shared canopy network,252 fitted neural coefficients plus18 exchange coefficients;90s recursive training with measured building boundary states. No validation configurations fitted. Fully autonomous validation required.')
  (folder/f'epoch{epoch}.json').write_text(json.dumps(payload));(ROOT/'results/recursive-canopy-constrained-training.json').write_text(json.dumps(dict(history=history,elapsed_seconds=time.time()-start),indent=2));print(epoch,history[-1]['loss'],round(time.time()-start,1),flush=True)
