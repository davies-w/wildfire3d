"""Fit response/transport on singles, then adapt transport on A/B pairs only.

Configuration-held-out validation selects checkpoints by autonomous rollout.
No test files are loaded. Prototype is canopy-only: no gas/flame-field claim.
"""
import argparse,copy,json,random,time
import numpy as np
import torch
from graph_model import ComponentGraph
from model_data import observation
from build import ROOT

def rate_groups(rate,d):
 out=[]
 for i in range(len(d['case']['trees'])):
  out.append(torch.stack([rate[(d['instance']==i)&(d['fuel']==k)].sum() for k in range(4)]))
 return torch.stack(out)

def window_loss(model,d,start,length=8):
 hidden=torch.zeros(len(d['xyz']),8);rate=torch.zeros(len(d['xyz']));loss=0.
 kw={k:d[k] for k in ['static','xyz','instance','heater_xyz']}
 for j in range(start,min(start+length,len(d['time'])-1)):
  dt=float(d['time'][j+1]-d['time'][j]);state=d['state'][j]
  nxt,hidden,rate,heat=model.step(**kw,state=state,hidden=hidden,fuel_rate=rate,heater_strength=d['schedule'][j],dt=dt,observed_heat=d['heat'][j])
  # Quantities have predeclared physical scaling, not fitted test statistics.
  loss=loss+(nxt[:,0]-d['state'][j+1,:,0]).square().mean()+5*(nxt[:,1]-d['state'][j+1,:,1]).square().mean()
  loss=loss+((heat-d['heat'][j])/100).square().mean()
  initial=torch.stack([torch.stack([d['static'][(d['instance']==i)&(d['fuel']==k),9].sum() for k in range(4)]) for i in range(len(d['case']['trees']))])
  loss=loss+((rate_groups(rate,d)-d['rates'][j+1])/(initial/180+.001)).square().mean()
 return loss/min(length,len(d['time'])-1-start)

@torch.no_grad()
def validate(model,ds):
 rows=[]
 for d in ds:
  state,heat,rate=model.rollout(**{k:d[k] for k in ['static','xyz','instance','heater_xyz']},schedule=d['schedule'])
  assert state.shape==d['state'].shape
  terr=float((state[:,:,0]-d['state'][:,:,0]).abs().mean()*1000);merr=float((state[:,:,1]-d['state'][:,:,1]).abs().mean());qerr=float((heat-d['heat'][:-1]).abs().mean())
  score=terr/1000+merr+qerr/100
  rows.append(dict(case=d['case']['case'],temperature_MAE_C=terr,mass_fraction_MAE=merr,heat_flux_MAE_kW_m2=qerr,selection_score=score))
 return float(np.mean([r['selection_score'] for r in rows])),rows

def fit(model,train,val,epochs,adapt=False):
 if adapt:
  for p in list(model.response.parameters())+list(model.output.parameters()):p.requires_grad_(False)
 optim=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=.002)
 best=float('inf');beststate=None;history=[];rng=random.Random(26)
 for epoch in range(epochs):
  model.train();order=list(range(len(train)));rng.shuffle(order);losses=[]
  for i in order:
   d=train[i];start=rng.randrange(max(1,len(d['time'])-8));optim.zero_grad();loss=window_loss(model,d,start);assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),2.);optim.step();losses.append(float(loss.detach()))
  if epoch%5==0 or epoch==epochs-1:
   model.eval();score,rows=validate(model,val);history.append(dict(epoch=epoch,training_loss=float(np.mean(losses)),validation_score=score,validation=rows))
   if score<best:best=score;beststate=copy.deepcopy(model.state_dict())
   print('EPOCH',epoch,'validation',score,flush=True)
 assert beststate is not None;model.load_state_dict(beststate);return history

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--epochs',type=int,default=100);args=p.parse_args();torch.set_num_threads(4);torch.manual_seed(26)
 cs=json.loads((ROOT/'cases.json').read_text());dev=[c for c in cs if c['split'] in ['train','validation']]
 for c in dev:assert (ROOT/'data/extracted'/(c['case']+'.npz')).exists(),c['case']
 ds={c['case']:observation(c) for c in dev};single_train=[ds[c['case']] for c in dev if c['family']=='single' and c['split']=='train'];single_val=[ds[c['case']] for c in dev if c['family']=='single' and c['split']=='validation']
 out=ROOT/'data/models';out.mkdir(exist_ok=True);m=ComponentGraph();history=fit(m,single_train,single_val,args.epochs);torch.save(m.state_dict(),out/'single-only.pt')
 pairs_train=[ds[c['case']] for c in dev if c['family'] in ['pair','control'] and c['split']=='train'];pairs_val=[ds[c['case']] for c in dev if c['family'] in ['pair','control'] and c['split']=='validation']
 before=validate(m,pairs_val);adapted=copy.deepcopy(m);h2=fit(adapted,pairs_train,pairs_val,args.epochs,adapt=True);torch.save(adapted.state_dict(),out/'pair-adapted.pt')
 (out/'training-report.json').write_text(json.dumps(dict(parameters=sum(p.numel() for p in m.parameters()),single_training=[d['case']['case'] for d in single_train],pair_training=[d['case']['case'] for d in pairs_train],single_history=history,pair_history=h2,zero_shot_pair_validation=before,adapted_pair_validation=validate(adapted,pairs_val),scope='Canopy regional temperature/mass and heat transfer only; not full gas/flame field. Configuration splits; teacher-forced short-window fitting, fully autonomous validation. Response weights frozen during pair adaptation. C has no pair/control training or validation.'),indent=2))
