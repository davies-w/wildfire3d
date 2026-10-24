"""Descriptive validation-only spatial residual association; no model fitting."""
from pathlib import Path
import json
import numpy as np
from scipy.stats import spearmanr
R=Path(__file__).resolve().parent;P=R.parent/'attempt20';a=np.load(P/'data/sequences.npz');sp=np.load(R/'data/spatial_candidates.npz')['values'];meta=json.loads((P/'schema.json').read_text());conf=a['configuration'];groups=np.unique(conf);out={};rows=[]
def group(x):return np.array([x[conf==c].mean(0) for c in groups])
def qt(y,t,q):
 c=np.r_[0,np.cumsum((y[1:]+y[:-1])*.5*np.diff(t))];return float(np.interp(q*c[-1],c,t)) if c[-1]>1e-8 else np.nan
for arm in ['control','thermal']:
 pred=np.zeros_like(a['state']);seen=[]
 for k in range(20):
  if ['control','thermal'][k%2]!=arm:continue
  v=np.load(P/f'data/collected/fold{k:02}-validation-predictions.npz');ids=v['case_indices'];assert set(ids)==set(meta['rotations'][k//2]['validation']);seen+=ids.tolist();pred[ids,0]=a['state'][ids,0];pred[ids,1:]=np.sinh(v['normalized_rollout']*v['std']+v['mean'])*v['physical_scales']
 assert sorted(seen)==list(range(520));assert np.isfinite(pred).all()
 truth=np.maximum(a['state'][:,:,2],0);raw=pred[:,:,2];pos=np.maximum(raw,0);t=a['time'];total=np.trapezoid(truth,t,axis=1);ptotal=np.trapezoid(pos,t,axis=1);err=np.trapezoid(abs(raw-truth),t,axis=1);quiet=truth<=1e-6;timing=[];late=[];shift=[];unshift=[];aligned=[]
 for i in range(520):
  timing.append([qt(pos[i],t[i],q)-qt(truth[i],t[i],q) for q in [.1,.5,.9]]);end=qt(truth[i],t[i],.99);tt=np.r_[end,t[i,t[i]>end]];late.append(max(0,np.trapezoid(np.interp(tt,t[i],pos[i])-np.interp(tt,t[i],truth[i]),tt)))
  grid=np.arange(10,171);yy=np.interp(grid,t[i],truth[i]);ee=np.array([np.mean(abs(np.interp(grid+s,t[i],pos[i])-yy)) for s in range(-10,11)]);j=int(ee.argmin());shift.append(j-10);unshift.append(ee[10]);aligned.append(ee[j])
 stats=dict(total_error_percent=float(100*group(abs(ptotal-total)).mean()/group(total).mean()),peak_error_percent=float(100*group(abs(pos.max(1)-truth.max(1))).mean()/group(truth.max(1)).mean()),fixed_time_error_percent=float(100*group(err).mean()/group(total).mean()),median_abs_timing_s=np.median(group(abs(np.array(timing))),axis=0).tolist(),late_excess_percent=float(100*group(np.array(late)).mean()/group(total).mean()),shift_error_reduction_percent=float(100*(1-group(np.array(aligned)).mean()/group(np.array(unshift)).mean())),quiet_error_share_percent=float(100*group(np.trapezoid(abs(raw-truth)*quiet,t,axis=1)).mean()/group(err).mean()))
 # Configurations, not frames/replicas, are statistical units. No local predictive model is fitted.
 # Within each time slice remove heating-strength-bin means, then summarize per configuration.
 residual=group(raw-truth);heat=group(a['state'][:,:,3]);dip=group(sp[:,:,2:]);strength=group(sp[:,:,1]);vec=dip/np.maximum(strength[:,:,None],.01);mag=np.linalg.norm(vec,axis=-1);tt=group(t);window=(tt>20)&(tt<=90)
 candidates=np.concatenate([vec,mag[:,:,None]],-1);rr=residual.copy();xx=candidates.copy()
 for j in range(91):
  bins=np.searchsorted(np.quantile(heat[:,j],np.linspace(0,1,11)[1:-1]),heat[:,j])
  for b in range(10):
   keep=bins==b
   if keep.any():rr[keep,j]-=rr[keep,j].mean();xx[keep,j]-=xx[keep,j].mean(0)
 den=window.sum(1);rs=(rr*window).sum(1)/den;xs=(xx*window[:,:,None]).sum(1)/den[:,None];signed=[float(spearmanr(xs[:,q],rs).statistic) for q in range(4)]
 absr=(abs(rr)*window).sum(1)/den;absc=[float(spearmanr(xs[:,q],absr).statistic) for q in range(4)]
 stats['spatial_association']=dict(window='20–90s; within-time heating-decile centering then per-configuration means',candidates=['centroid_offset_x','centroid_offset_y','centroid_offset_z','offset_norm'],signed_error_spearman=signed,absolute_error_spearman=absc,scope='Descriptive validation association only; true observed spatial moments, not autonomous predicted features. Does not prove state sufficiency or causality; remaining geometry/forcing confounding possible.')
 out[arm]=stats
 for i in range(520):rows.append(dict(arm=arm,case=i,configuration=int(conf[i]),true_total_kg=float(total[i]),predicted_positive_total_kg=float(ptotal[i]),fixed_time_abs_integral_kg=float(err[i]),timing_errors_s=timing[i],best_shift_s=shift[i]))
(R/'data/validation_residuals').mkdir(exist_ok=True);(R/'data/validation_residuals/report.json').write_text(json.dumps(dict(summary=out,rows=rows,scope='Validation only, selected checkpoints; no test reads, no fitting, no causal claim. Full180s initial-state rollouts.'),indent=2));print(json.dumps(out,indent=2))
