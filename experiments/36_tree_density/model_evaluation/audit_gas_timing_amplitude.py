"""Frozen model TRAIN-only gas timing/amplitude decomposition; no fitting or correction."""
from pathlib import Path
import ast,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02'
sys.path.insert(0,str(D));from model import Transition
torch.set_num_threads(4)
a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());ids=torch.tensor(meta['rotations'][0]['train']);raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;model=Transition('gated');model.load_state_dict(ck['model']);model.eval()
names={'history_at','advance','predictions'};nodes=[n for n in ast.parse((D/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);ns=dict(torch=torch,external=external);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-inference','exec'),ns)

mask=times[ids,1:]<=32.2
truth=raw[ids,1:,2].numpy();tt=times[ids,1:].numpy();reports={};rows={}
with torch.inference_mode():
 for mode in ['one_step','rollout']:
  pred=ns['predictions'](model,z,ids,mode=='rollout');gas=(torch.sinh(pred[:,:,2]*std[2]+mean[2])*scale[2]).numpy();assert np.isfinite(gas).all();cases=[]
  for j,i in enumerate(ids.tolist()):
   startup=tt[j]<=32.2;t=tt[j,startup];actual=truth[j,startup];forecast=gas[j,startup];pt=int(actual.argmax());pp=int(forecast.argmax());den=max(float(raw[i,:,2].max()),.01)
   # Fixed central interval gives every candidate lag the same targets and no extrapolation.
   central=(t>=8)&(t<=26.2);target=actual[central];tc=t[central];lags=np.arange(-6,7,2);errors=np.array([np.abs(np.interp(tc+lag,tt[j],gas[j])-target).mean() for lag in lags]);zero=int(np.where(lags==0)[0][0]);best=int(errors.argmin())
   cases.append(dict(case=meta['cases'][i]['case'],configuration=int(a['configuration'][i]),true_startup_peak_kg_s=float(actual[pt]),pred_startup_peak_kg_s=float(forecast[pp]),peak_amplitude_signed_fraction=(float(forecast[pp])-float(actual[pt]))/den,peak_time_error_s=float(t[pp]-t[pt]),error_at_true_peak_fraction=(float(forecast[pt])-float(actual[pt]))/den,central_MAE_kg_s=float(errors[zero]),oracle_shift_MAE_kg_s=float(errors[best]),oracle_shift_s=int(lags[best]),oracle_shift_relative_MAE_reduction=float(1-errors[best]/max(errors[zero],1e-12))))
  def summary(key):
   # Average replicas first so every physical configuration has equal influence.
   groups={}
   for row in cases:groups.setdefault(row['configuration'],[]).append(row[key])
   v=np.array([np.mean(x) for x in groups.values()]);return dict(median=float(np.median(v)),p10=float(np.quantile(v,.1)),p90=float(np.quantile(v,.9)),mean=float(v.mean()))
  reports[mode]={k:summary(k) for k in ['peak_amplitude_signed_fraction','peak_time_error_s','error_at_true_peak_fraction','central_MAE_kg_s','oracle_shift_MAE_kg_s','oracle_shift_relative_MAE_reduction']};rows[mode]=cases
out=dict(train_only=True,optimizer_updates=0,checkpoint_epoch=ck['epoch'],histories=len(ids),reports=reports,scope='Frozen inference only. Startup peaks use actual saved endpoints<=32.2s, amplitudes normalized by full true gas peak with0.01kg/s floor. Oracle lag evaluates fixed shifts -6,-4,-2,0,2,4,6s using linear interpolation and central target endpoints8..26.2s only, no extrapolation. Lag is chosen with each case truth: optimistic diagnostic, NEVER a forecast, learned correction, model selection or validation. Summaries average replicas within physical configuration before quantiles. No validation/test evaluation. No evidence that missing elapsed-time input causes the errors.',cases=rows)
(R/'results/gas-timing-amplitude-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='cases'},indent=2))
