"""Inference-only validation burn audit; frozen selected checkpoints, no fitting."""
from pathlib import Path
import json
import numpy as np
import torch
from model import Transition
R=Path(__file__).resolve().parent
meta=json.loads((R/'schema.json').read_text());a=np.load(R/'data/sequences.npz')
torch.set_num_threads(4)
raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);scale=torch.tensor(meta['physical_encoding_scales'])
dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt
external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales'])
rows=[];saved={}
def integ(y,t):return float(np.trapezoid(y,t))
def quantile_time(y,t,q):
 c=np.r_[0,np.cumsum((y[:-1]+y[1:])*.5*np.diff(t))]
 return float(np.interp(q*c[-1],c,t)) if c[-1]>1e-8 else None
with torch.inference_mode():
 for k in range(20):
  kind=['mlp','gru'][k%2];rot=meta['rotations'][k//2];ids=torch.tensor(rot['validation'])
  ck=torch.load(R/f'data/collected/fold{k:02}-selected.pt',map_location='cpu',weights_only=False)
  model=Transition(kind);model.load_state_dict(ck['model']);model.eval();mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std
  history=z[ids,0,None,:].expand(-1,4,-1).clone();memory=None;pred=[raw[ids,0].numpy()]
  for j in range(90):
   state,memory=model.step(history,external[ids,j],memory);history=torch.cat([history[:,1:],state[:,None]],1);pred.append((torch.sinh(state*std+mean)*scale).numpy())
  pred=np.stack(pred,1);assert np.isfinite(pred).all()
  saved[f'fold{k:02}_pred']=pred;saved[f'fold{k:02}_ids']=ids.numpy()
  for n,i in enumerate(ids.tolist()):
   t=a['time'][i].astype(float);truth=np.maximum(a['state'][i,:,2],0);p=pred[n,:,2].astype(float);positive=np.maximum(p,0)
   total=integ(truth,t);ptotal=integ(positive,t);peak=float(truth.max());quiet=truth<=1e-6
   row=dict(arm=kind,rotation=k//2,case=i,configuration=int(a['configuration'][i]),truth_total=total,pred_total=ptotal,total_abs_error=abs(ptotal-total),truth_peak=peak,peak_abs_error=abs(float(positive.max())-peak),raw_abs_error_integral=integ(abs(p-truth),t),positive_abs_error_integral=integ(abs(positive-truth),t),negative_integral=integ(np.maximum(-p,0),t),quiet_fraction=float(quiet.mean()),quiet_abs_error_integral=integ(abs(p-truth)*quiet,t),active_abs_error_integral=integ(abs(p-truth)*(~quiet),t))
   for q in [10,50,90,99]:
    tt=quantile_time(truth,t,q/100);pp=quantile_time(positive,t,q/100);row[f't{q}_truth']=tt;row[f't{q}_delta']=None if tt is None or pp is None else pp-tt
   end=row['t99_truth']
   if end is not None:
    tailt=np.r_[end,t[t>end]];row['late_excess_mass']=max(0,integ(np.interp(tailt,t,positive),tailt)-integ(np.interp(tailt,t,truth),tailt))
   else:row['late_excess_mass']=None
   grid=np.arange(10,170.001,1.);target=np.interp(grid,t,truth);shifts=np.arange(-10,11,1.)
   errors=np.array([np.mean(abs(np.interp(grid+s,t,positive)-target)) for s in shifts]);best=int(errors.argmin());row.update(shift_seconds=float(shifts[best]),unshifted_common_error=float(errors[10]),shifted_common_error=float(errors[best]))
   rows.append(row)
  print('evaluated',k,flush=True)
def groups(rr,key):
 out=[]
 for c in sorted(set(r['configuration'] for r in rr)):
  v=[r[key] for r in rr if r['configuration']==c and r[key] is not None]
  if v:out.append(np.mean(v))
 return np.array(out)
summary={}
for arm in ['mlp','gru']:
 rr=[r for r in rows if r['arm']==arm];burn=[r for r in rr if r['truth_total']>=.01];s={ 'histories':len(rr),'configurations':len(set(r['configuration'] for r in rr)), 'burn_histories_total_at_least_10g':len(burn)}
 for name,num,den in [('total_amount_error_percent','total_abs_error','truth_total'),('peak_error_percent','peak_abs_error','truth_peak'),('fixed_time_error_percent','raw_abs_error_integral','truth_total'),('late_excess_percent','late_excess_mass','truth_total')]:s[name]=float(100*groups(rr,num).mean()/groups(rr,den).mean())
 s['timing_burn_only']={str(q):{'median_absolute_seconds':float(np.median(abs(groups(burn,f't{q}_delta')))),'median_signed_seconds':float(np.median(groups(burn,f't{q}_delta')))} for q in [10,50,90]}
 s['shift_error_reduction_percent']=float(100*(1-groups(rr,'shifted_common_error').mean()/groups(rr,'unshifted_common_error').mean()))
 s['median_absolute_best_shift_seconds']=float(np.median(abs(groups(burn,'shift_seconds'))))
 s['quiet_fraction']=float(groups(rr,'quiet_fraction').mean());s['quiet_share_absolute_error_percent']=float(100*groups(rr,'quiet_abs_error_integral').mean()/groups(rr,'raw_abs_error_integral').mean())
 summary[arm]=s
out=R/'data/validation_burn_audit';out.mkdir(exist_ok=True);np.savez_compressed(out/'predictions.npz',**saved);(out/'metrics.json').write_text(json.dumps({'summary':summary,'rows':rows,'method':'Full autonomous validation rollouts from true initial state. Configuration balanced. Positive part used only for physical amount/timing diagnostics; raw fixed-time errors and negative release preserved. T99 defines end; not necessarily cessation. Shifts +-10s on fixed10..170s grid, diagnostic fitted against truth, not deployable correction. Timing excludes truth totals below10g. Validation selected these checkpoints, so not independent test.'},indent=2));print(json.dumps(summary,indent=2))
