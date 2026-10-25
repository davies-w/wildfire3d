"""Post-training burn timing and magnitude audit; no fitting or model selection."""
from pathlib import Path
import json
import numpy as np
from scipy.stats import spearmanr
R=Path(__file__).resolve().parent;P=R;a=np.load(P/'data/sequences.npz');meta=json.loads((P/'schema.json').read_text());conf=a['configuration'];groups=np.unique(conf);out={};rows=[]
def group(x):return np.array([x[conf==c].mean(0) for c in groups])
def qt(y,t,q):
 c=np.r_[0,np.cumsum((y[1:]+y[:-1])*.5*np.diff(t))];return float(np.interp(q*c[-1],c,t)) if c[-1]>1e-8 else np.nan
import sys
split=sys.argv[1]
assert split in ['validation','test']
for arm in ['scalar','spatial']:
 pred=np.zeros_like(a['state']);seen=[]
 for k in range(20):
  if ['scalar','spatial'][k%2]!=arm:continue
  v=np.load(P/f'data/collected/fold{k:02}-{split}-predictions.npz');ids=v['case_indices'];assert set(ids)==set(meta['rotations'][k//2][split]);seen+=ids.tolist();pred[ids,0]=a['state'][ids,0];pred[ids,1:]=np.sinh(v['normalized_rollout']*v['std']+v['mean'])*v['physical_scales']
 assert sorted(seen)==list(range(520));assert np.isfinite(pred).all()
 truth=np.maximum(a['state'][:,:,2],0);raw=pred[:,:,2];pos=np.maximum(raw,0);t=a['time'];total=np.trapezoid(truth,t,axis=1);ptotal=np.trapezoid(pos,t,axis=1);err=np.trapezoid(abs(raw-truth),t,axis=1);quiet=truth<=1e-6;timing=[];late=[];shift=[];unshift=[];aligned=[]
 for i in range(520):
  timing.append([qt(pos[i],t[i],q)-qt(truth[i],t[i],q) for q in [.1,.5,.9]]);end=qt(truth[i],t[i],.99);tt=np.r_[end,t[i,t[i]>end]];late.append(max(0,np.trapezoid(np.interp(tt,t[i],pos[i])-np.interp(tt,t[i],truth[i]),tt)))
  grid=np.arange(10,171);yy=np.interp(grid,t[i],truth[i]);ee=np.array([np.mean(abs(np.interp(grid+s,t[i],pos[i])-yy)) for s in range(-10,11)]);j=int(ee.argmin());shift.append(j-10);unshift.append(ee[10]);aligned.append(ee[j])
 stats=dict(total_error_percent=float(100*group(abs(ptotal-total)).mean()/group(total).mean()),peak_error_percent=float(100*group(abs(pos.max(1)-truth.max(1))).mean()/group(truth.max(1)).mean()),fixed_time_error_percent=float(100*group(err).mean()/group(total).mean()),median_abs_timing_s=np.median(group(abs(np.array(timing))),axis=0).tolist(),late_excess_percent=float(100*group(np.array(late)).mean()/group(total).mean()),shift_error_reduction_percent=float(100*(1-group(np.array(aligned)).mean()/group(np.array(unshift)).mean())),quiet_error_share_percent=float(100*group(np.trapezoid(abs(raw-truth)*quiet,t,axis=1)).mean()/group(err).mean()))
 stats['physical_mae_by_feature']=group(abs(pred[:,1:]-a['state'][:,1:]).mean(1)).mean(0).tolist()
 stats['negative_fraction_first3']=group((pred[:,1:,:3]<0).mean(1)).mean(0).tolist()
 stats['negative_mean_magnitude_first3']=group(np.maximum(-pred[:,1:,:3],0).mean(1)).mean(0).tolist()
 stats['mass_increase_mean_kg']=group(np.maximum(np.diff(pred[:,:,:2],axis=1),0).mean(1)).mean(0).tolist()
 out[arm]=stats
 for i in range(520):rows.append(dict(arm=arm,case=i,configuration=int(conf[i]),true_total_kg=float(total[i]),predicted_positive_total_kg=float(ptotal[i]),fixed_time_abs_integral_kg=float(err[i]),timing_errors_s=timing[i],best_shift_s=shift[i]))
(R/f'results/posthoc-{split}.json').write_text(json.dumps(dict(summary=out,scope='Post-training selected models. Full180s initial-state rollouts. Equal configuration weighting; raw fixed-time errors; positive release used for amounts and timing; best +/-10s shift is optimistic descriptive alignment, not a forecast.'),indent=2));print(json.dumps(out,indent=2))
