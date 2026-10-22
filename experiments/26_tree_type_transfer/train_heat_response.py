"""Conditional component response to recorded FDS radiation/convection.
Not autonomous composition: convection contains the true FDS temperature coupling.
No pair/test data in training or checkpoint selection. All original hashes immutable.
"""
import argparse,json,time,hashlib
import numpy as np
import torch
from torch import nn
from build import ROOT,CLASSES
from model_data import observation
TT=np.arange(0,182,2)
OUT=ROOT/'data/heat-response'

def component_records(c):
 d=observation(c);s=d['state'].numpy();q=d['heat'].numpy();r=d['rates'].numpy();inst=d['instance'].numpy();records=[]
 for i,tree in enumerate(c['trees']):
  mask=inst==i;n=int(mask.sum());state=s[:,mask];heat=q[:,mask]
  Y=np.column_stack([np.interp(TT,d['time'],state[:,j,k]) for k in range(2) for j in range(n)])
  Q=np.stack([np.interp(TT[:-1],d['time'],heat[:,j,k]) for j in range(n) for k in range(2)],1).reshape(90,n,2)
  rates=np.stack([np.interp(TT[:-1],d['time'],r[:,i,k]) for k in range(4)],1)
  m0=d['static'][mask,9].numpy();fuel=d['fuel'][mask].numpy()
  records.append(dict(case=c['case'],split=c['split'],family=c['family'],instance=i,type=tree['type'],n=n,y=Y,q=Q,rates=rates,m0=m0,fuel=fuel))
 return records

class HeatResponse(nn.Module):
 def __init__(self,n,m0,fuel):
  super().__init__();self.n=n;self.cell=nn.GRUCell(4*n,32);self.head=nn.Linear(32,2*n+4)
  self.register_buffer('m0',torch.tensor(m0,dtype=torch.float32));self.register_buffer('fuelmap',torch.tensor(np.eye(4)[fuel],dtype=torch.float32))
  nn.init.normal_(self.head.weight,std=.01)
  with torch.no_grad():self.head.bias[:n].fill_(-3.9);self.head.bias[n:2*n].fill_(-5.);self.head.bias[2*n:].zero_()
 def forward(self,Q):
  b=len(Q);s=torch.cat([torch.zeros(b,self.n),torch.ones(b,self.n)],1);hidden=torch.zeros(b,32);states=[s];rates=[]
  for j in range(Q.shape[1]):
   forcing=torch.asinh(Q[:,j].reshape(b,-1)/10)
   hidden=self.cell(torch.cat([s,forcing],1),hidden);v=self.head(hidden)
   temp=torch.nn.functional.softplus(v[:,:self.n])-.02
   mass=s[:,self.n:]*torch.exp(-.1*torch.sigmoid(v[:,self.n:2*self.n]))
   loss=(s[:,self.n:]-mass)*self.m0;fuel_rate=(loss@self.fuelmap)*torch.sigmoid(v[:,2*self.n:])/2
   s=torch.cat([temp,mass],1);states.append(s);rates.append(fuel_rate)
  return torch.stack(states,1),torch.stack(rates,1)

def metrics(p,r,d):
 n=d['n'];m0class=d['m0']@np.eye(4)[d['fuel']];tempdiff=abs(p[:,:n]-d['y'][:,:n]);active=(p[:,:n]>.08)|(d['y'][:,:n]>.08)
 return dict(case=d['case'],type=d['type'],instance=d['instance'],family=d['family'],split=d['split'],temperature_MAE_C=float(tempdiff.mean()*1000),active_union_temperature_MAE_C=float(tempdiff[active].mean()*1000) if active.any() else None,mass_fraction_MAE=float(abs(p[:,n:]-d['y'][:,n:]).mean()),fuel_cumulative_fraction_MAE=float(abs(np.cumsum(r*2,axis=0)/m0class-np.cumsum(d['rates']*2,axis=0)/m0class).mean()),fuel_rate_MAE_kg_s=float(abs(r.sum(1)-d['rates'].sum(1)).mean()),predicted_fuel_kg=float(r.sum()*2),FDS_sampled_fuel_kg=float(d['rates'].sum()*2),mass_bound_violations=int(((p[:,n:]< -1e-6)|(p[:,n:]>1+1e-6)).sum()),mass_increase_violations=int((np.diff(p[:,n:],axis=0)>1e-6).sum()))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--epochs',type=int,default=2000);args=ap.parse_args();torch.set_num_threads(1);OUT.mkdir(exist_ok=False)
 freeze=json.loads((ROOT/'results/prediction-freeze.json').read_text())
 for f,h in freeze['files'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
 cases=json.loads((ROOT/'cases.json').read_text());singles=[component_records(c)[0] for c in cases if c['family']=='single'];report=dict(types=[],scope='Conditional on FDS radiation and convection histories; self-fed temperatures/masses, not autonomous FDS-free composition. Three separate fixed-type models. Pair data excluded from fitting/selection. No new test outputs.',chemical_power_definition='Predicted fuel-vapor rate *17425 kJ/kg: potential chemical power, NOT actual gas heat release or transferred heat.',time_sampling='FDS states interpolated to2s; rates left-sampled/integrated at2s for both fitting and comparisons; raw high-frequency devices preserved.',constraints='Mass nonincreasing in[0,1], T>=0C; class fuel release <= predicted wet/solid mass loss. Not energy conservation.')
 for typ in 'ABC':
  torch.manual_seed(26);ds=[d for d in singles if d['type']==typ];tr=[d for d in ds if d['split']=='train'];m=HeatResponse(ds[0]['n'],ds[0]['m0'],ds[0]['fuel']);n=m.n
  Q=torch.tensor(np.array([d['q'] for d in tr]),dtype=torch.float32);Y=torch.tensor(np.array([d['y'] for d in tr]),dtype=torch.float32);R=torch.tensor(np.array([d['rates'] for d in tr]),dtype=torch.float32);classmass=m.m0@m.fuelmap;allQ=torch.tensor(np.array([d['q'] for d in ds]),dtype=torch.float32)
  opt=torch.optim.Adam(m.parameters(),lr=.003);best=None;history=[];start=time.monotonic()
  for epoch in range(args.epochs+1):
   opt.zero_grad();p,r=m(Q);cum=torch.cumsum(r*2,dim=1)/classmass;truthcum=torch.cumsum(R*2,dim=1)/classmass
   loss=((p[:,:,:n]-Y[:,:,:n])**2).mean()+((p[:,:,n:]-Y[:,:,n:])**2).mean()+((cum-truthcum)**2).mean()+.02*((r-R)/(classmass/60)) .square().mean()
   loss.backward();nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
   if epoch%20==0 or epoch==args.epochs:
    with torch.no_grad():ps,rs=m(allQ);ps=ps.numpy();rs=rs.numpy()
    rows=[metrics(p,r,d) for p,r,d in zip(ps,rs,ds)];v=[x for x in rows if x['split']=='validation'];score=float(np.mean([x['temperature_MAE_C']/1000+x['mass_fraction_MAE']+x['fuel_cumulative_fraction_MAE'] for x in v]));history.append(dict(epoch=epoch,train_loss=float(loss.detach()),validation_score=score))
    if best is None or score<best[0]:best=(score,epoch,{k:v.detach().clone() for k,v in m.state_dict().items()},rows,ps.copy(),rs.copy())
   if time.monotonic()-start>150:break
  torch.save(best[2],OUT/f'{typ}.pt')
  for d,p,r in zip(ds,best[4],best[5]):np.savez_compressed(OUT/f"{d['case']}__{d['instance']}.npz",time=TT,state=p,truth=d['y'],heat_inputs=d['q'],fuel_rate=r,FDS_fuel_rate=d['rates'],potential_chemical_power_kW=r.sum(1)*17425)
  report['types'].append(dict(type=typ,parameters=sum(p.numel() for p in m.parameters()),epochs_completed=epoch+1,selected_epoch=best[1],history=history,metrics=best[3],fit_seconds=time.monotonic()-start))
  (ROOT/'results/heat-response.json').write_text(json.dumps(report,indent=2));print(typ,'selected',best[1],'score',best[0],'seconds',time.monotonic()-start,flush=True)
 # Freeze before inspecting any familiar-pair response outputs in this new diagnostic.
 frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in list(OUT.glob('*.pt'))+[ROOT/'train_heat_response.py']}
 (ROOT/'results/heat-response-freeze.json').write_text(json.dumps(dict(created_unix=time.time(),files=frozen,selection='isolated validation only'),indent=2))
 pairrows=[]
 for c in cases:
  if c['family']=='single' or c['split'] not in ['train','validation']:continue
  for d in component_records(c):
   m=HeatResponse(d['n'],d['m0'],d['fuel']);m.load_state_dict(torch.load(OUT/f"{d['type']}.pt",weights_only=True))
   with torch.no_grad():p,r=m(torch.tensor(d['q'][None],dtype=torch.float32));p=p[0].numpy();r=r[0].numpy()
   np.savez_compressed(OUT/f"{d['case']}__{d['instance']}.npz",time=TT,state=p,truth=d['y'],heat_inputs=d['q'],fuel_rate=r,FDS_fuel_rate=d['rates'],potential_chemical_power_kW=r.sum(1)*17425)
   pairrows.append(metrics(p,r,d))
 report['familiar_pair_control_conditional_check']=pairrows
 (ROOT/'results/heat-response.json').write_text(json.dumps(report,indent=2));print('DONE',flush=True)
if __name__=='__main__':main()
