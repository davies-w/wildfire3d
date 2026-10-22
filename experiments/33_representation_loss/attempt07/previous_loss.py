"""Physical-unit loss repair. Development data only; no test ingestion."""
import json,time,copy,argparse
import numpy as np
import torch
from original_cnn import CNN,cond,encode,load,loss,ROOT

def quantities(p):
 return 20+100*torch.sinh(p[:,0].clamp(-5,5)),10*torch.expm1(p[:,1].clamp(0,10)),2*torch.expm1(p[:,5].clamp(0,10))
def objective(p,y):
 t,q,g=quantities(p);ty,qy,gy=quantities(y)
 dims=(1,2,3);total=q.sum(dims)*.125;target=qy.sum(dims)*.125
 integral=(torch.log1p(total)-torch.log1p(target)).square().mean()
 spatial=((q-qy).abs().sum(dims)*.125/(target+100)).mean()
 peak=((t.amax(dims)-ty.amax(dims))/500).square().mean()
 radiation=((g-gy).abs().sum(dims)/(gy.sum(dims)+1000)).mean()
 return loss(p,y)+.1*integral+.05*spatial+.1*peak+.1*radiation

def assess(model,cases,device):
 rows=[]
 with torch.no_grad():
  for c in cases:
   a,ts=load(c)
   for k in [5,10,15,25,45,60,75,90]:
    y=torch.from_numpy(encode(a[k:k+1],c['wind_speed'])).to(device);p=model(torch.from_numpy(cond(c,ts[k:k+1])).to(device))
    t,q,g=quantities(p);ty,qy,gy=quantities(y);mask=(t>50)|(ty>50)
    rows.append(dict(case=c['case'],time_s=float(ts[k]),objective=float(objective(p,y)),heat_kW=float(q.sum()*.125),truth_heat_kW=float(qy.sum()*.125),hot_MAE_C=float((t-ty).abs()[mask].mean()) if mask.any() else 0,peak_C=float(t.max()),truth_peak_C=float(ty.max()),radiation_relative_L1=float((g-gy).abs().sum()/(gy.sum()+1e-8))))
 return dict(score=float(np.mean([r['objective'] for r in rows])),rows=rows)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--steps',type=int,default=4000);ap.add_argument('--capacity',action='store_true');args=ap.parse_args()
 torch.manual_seed(2801);rng=np.random.default_rng(2801);device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
 cs=json.loads((ROOT/'cases.json').read_text());train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation']
 name='capacity' if args.capacity else 'physical';train=train[:4] if args.capacity else train
 model=CNN().to(device);model.load_state_dict(torch.load(ROOT/'data/models/original.pt',weights_only=True,map_location=device));opt=torch.optim.AdamW(model.parameters(),lr=.00015,weight_decay=1e-5)
 arrays=[load(c) for c in train];evaluated=train if args.capacity else val;baseline=assess(model,evaluated,device);best=baseline['score'];state=copy.deepcopy(model.state_dict());selected=0;history=[];started=time.monotonic()
 for step in range(1,args.steps+1):
  j=int(rng.integers(len(train)));c=train[j];a,ts=arrays[j];ix=rng.integers(len(ts),size=2)
  y=torch.from_numpy(encode(a[ix],c['wind_speed'])).to(device);p=model(torch.from_numpy(cond(c,ts[ix])).to(device));l=objective(p,y);opt.zero_grad();l.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
  if step%400==0 or step==args.steps:
   result=assess(model,evaluated,device);history.append(dict(step=step,score=result['score']));print(name,step,result['score'],flush=True)
   if result['score']<best:best=result['score'];state=copy.deepcopy(model.state_dict());selected=step
   (ROOT/f'results/{name}-progress.json').write_text(json.dumps(dict(baseline=baseline['score'],history=history,elapsed_s=time.monotonic()-started),indent=2))
 model.load_state_dict(state);torch.save(state,ROOT/f'data/models/{name}.pt');final=assess(model,evaluated,device)
 (ROOT/f'results/{name}.json').write_text(json.dumps(dict(baseline=baseline,final=final,selected_step=selected,history=history,training_cases=[c['case'] for c in train],evaluation_cases=[c['case'] for c in evaluated],elapsed_s=time.monotonic()-started),indent=2))
 print('DONE',name,selected,best,flush=True)
if __name__=='__main__':main()
