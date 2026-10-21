"""Complete training/validation trajectories; never opens old test fields."""
import argparse,json,time,math,hashlib
import numpy as np
import torch
from original_cnn import ROOT,CNN,load,prediction

def metrics(a,b,t):
 out={};ambient=a[0,5]
 for window,sel in [('all',t>=0),('post_source',t>=22),('late',t>=120)]:
  x=a[sel];y=b[sel];hot=(x[:,0]>50)|(y[:,0]>50);q=x[:,1].sum((1,2,3))*.125;qb=y[:,1].sum((1,2,3))*.125;gx=np.maximum(x[:,5]-ambient,0).sum(0);gy=np.maximum(y[:,5]-ambient,0).sum(0);fx=x[:,1]>10;fy=y[:,1]>10;union=fx|fy
  out[window]=dict(hot_MAE_C=float(abs(x[:,0]-y[:,0])[hot].mean()) if hot.any() else 0,temperature_MAE_C=float(abs(x[:,0]-y[:,0]).mean()),HRR_curve_relative_L1=float(abs(q-qb).sum()/max(q.sum(),1e-8)),radiation_dose_relative_L1=float(abs(gx-gy).sum()/max(gx.sum(),1e-8)),peak_error_C=float(abs(x[:,0].max()-y[:,0].max())),truth_peak_C=float(x[:,0].max()),predicted_peak_C=float(y[:,0].max()),truth_mean_HRR_kW=float(q.mean()),predicted_mean_HRR_kW=float(qb.mean()),velocity_MAE_m_s=float(np.sqrt(((x[:,2:5]-y[:,2:5])**2).sum(1)).mean()),flame_IoU=float((fx&fy).sum()/union.sum()) if union.any() else None,minimum_C=float(y[:,0].min()),truth_minimum_C=float(x[:,0].min()),subzero_fraction=float((y[:,0]<0).mean()))
  rise=np.abs(x[:,0]-20);terr=np.abs(x[:,0]-y[:,0]);truthhot=x[:,0]>50
  def percent(num,den):return float(100*num/den) if den>1e-8 else None
  out[window].update(temperature_rise_relative_L1_percent=percent(terr.sum(),rise.sum()),truth_hot_temperature_relative_L1_percent=percent(terr[truthhot].sum(),rise[truthhot].sum()),union_hot_temperature_relative_L1_percent=percent(terr[hot].sum(),rise[hot].sum()),HRR_curve_relative_L1_percent=percent(abs(q-qb).sum(),q.sum()),radiation_dose_relative_L1_percent=percent(abs(gx-gy).sum(),gx.sum()),peak_temperature_rise_error_percent=percent(abs(x[:,0].max()-y[:,0].max()),abs(x[:,0].max()-20)),velocity_vector_relative_L1_percent=percent(np.sqrt(((x[:,2:5]-y[:,2:5])**2).sum(1)).sum(),np.sqrt((x[:,2:5]**2).sum(1)).sum()))
 return out

def main():
 from models import make
 ap=argparse.ArgumentParser();ap.add_argument('name',choices=['previous','bound_only','bounded','heads','strength_only','interpolation']);ap.add_argument('--device',choices=['cpu','mps','auto'],default='auto');args=ap.parse_args();name=args.name;
 weights=[ROOT/'data/models/previous.pt']+([ROOT/f'data/models/{name}.pt'] if name in ['bounded','heads'] else [])+([ROOT/'data/models/strength.pt'] if name in ['heads','strength_only'] else []);deps=weights+[ROOT/'evaluate.py',ROOT/'models.py',ROOT/'cases.json',ROOT/'results/reuse.json'];fingerprint={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps};cached=ROOT/f'results/{name}-evaluation.json'
 if cached.exists() and json.loads(cached.read_text()).get('fingerprint')==fingerprint:print('Reused verified evaluation',name,flush=True);return
 cs=json.loads((ROOT/'cases.json').read_text());train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation'];rows=[];histories=[];device=torch.device(('mps' if torch.backends.mps.is_available() else 'cpu') if args.device=='auto' else args.device)
 if name!='interpolation':
  if name=='previous':m=CNN();m.load_state_dict(torch.load(ROOT/'data/models/previous.pt',map_location='cpu',weights_only=True))
  else:
   m=make('bounded' if name=='bound_only' else 'heads' if name=='strength_only' else name)
   if name not in ['bound_only','strength_only']:m.load_state_dict(torch.load(ROOT/f'data/models/{name}.pt',map_location='cpu',weights_only=True))
  m=m.to(device);m.eval()
 for c in (val if name=='interpolation' else cs):
  av,t=load(c);a=np.array(av)
  if name=='interpolation':
   feat=lambda z:np.array([z['wind_speed']/4,math.cos(math.radians(z['angle_deg'])),math.sin(math.radians(z['angle_deg']))]);ds=np.array([np.linalg.norm(feat(c)-feat(z)) for z in train]);ix=np.argsort(ds)[:3];weights=1/np.maximum(ds[ix],.01)**2;weights/=weights.sum();b=None
   for j,w in zip(ix,weights):
    ar,tr=load(train[j]);ids=abs(tr[:,None]-t).argmin(0);term=np.array(ar[ids]);term[:,2]-=train[j]['wind_speed'];term*=w;b=term if b is None else b+term
   b[:,2]+=c['wind_speed']
  else:b=prediction(m,c,t)
  row=dict(case=c['case'],split=c['split'],model=name,**metrics(a,b,t));rows.append(row)
  histories.append(dict(case=c['case'],split=c['split'],time_s=t.tolist(),truth_HRR_kW=(a[:,1].sum((1,2,3))*.125).tolist(),predicted_HRR_kW=(b[:,1].sum((1,2,3))*.125).tolist(),truth_peak_C=a[:,0].max((1,2,3)).tolist(),predicted_peak_C=b[:,0].max((1,2,3)).tolist()))
  if c in val[:2]:np.save(ROOT/f"data/validation_predictions/{name}_{c['case']}.npy",b)
  print('Evaluated',name,c['case'],flush=True)
 summary={}
 for split in ['train','validation']:
  rr=[r for r in rows if r['split']==split]
  if not rr:continue
  summary[split]={}
  for window in ['all','post_source','late']:
   summary[split][window]={k:float(np.mean([r[window][k] for r in rr if r[window][k] is not None])) if any(r[window][k] is not None for r in rr) else None for k in rr[0][window]}
 (ROOT/f'results/{name}-evaluation.json').write_text(json.dumps(dict(rows=rows,summary=summary,histories=histories,fingerprint=fingerprint,device=str(device)),indent=2));print('COMPLETE',name,json.dumps(summary.get('validation',{}).get('post_source',{})),flush=True)
if __name__=='__main__':main()
