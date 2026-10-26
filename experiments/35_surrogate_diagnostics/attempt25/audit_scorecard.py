"""Scenario distributions and event diagnostics from saved forecasts; no fitting."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent;a=np.load(R/'data/sequences.npz');conf=a['configuration'];truth=a['state'];labels=a['activity_labels'];report=json.loads((R/'data/collected/report.json').read_text());out={'distributions':{},'events':{}}
def timing(q,t,f):
 c=np.r_[0,np.cumsum((q[1:]+q[:-1])*.5*np.diff(t))]
 return float(np.interp(f*c[-1],c,t)) if c[-1]>1e-8 else np.nan
def grouped(values,ids):return np.array([values[conf[ids]==c].mean(0) for c in np.unique(conf[ids])])
fulltruth=truth
for kind in range(1,9):
 truth=fulltruth
 tests=[t for t in report['tests'] if t['training_fold_count']==kind];out['distributions'][kind]={}
 for h in [1,4,8,16,45]:
  records={p:[] for p in ['active','quiet','weak','transition']}
  for test in tests:
   v=np.load(R/f"data/collected/fold{test['fold']:02}-horizon{h:02}-predictions.npz");ids=v['case_indices'];p=v['predicted_physical'];target=truth[ids,h:];base=truth[ids,:91-h];assert p.shape==target.shape
   w=np.lib.stride_tricks.sliding_window_view(labels[ids],h,axis=1)
   active=np.isin(w,[1,2]).all(-1);quiet=(w==0).all(-1);weak=(w==3).all(-1);masks=dict(active=active,quiet=quiet,weak=weak,transition=~(active|quiet|weak))
   for phase,mask in masks.items():
    count=mask.sum(1);keep=count>0
    if not keep.any():continue
    e=(abs(p-target)*mask[:,:,None]).sum(1)[keep]/count[keep,None];b=(abs(base-target)*mask[:,:,None]).sum(1)[keep]/count[keep,None]
    cg=np.unique(conf[ids[keep]])
    for c,x,y in zip(cg,grouped(e,ids[keep]),grouped(b,ids[keep])):records[phase].append(dict(configuration=int(c),rotation=test['rotation'],model_MAE=x.tolist(),baseline_MAE=y.tolist()))
  out['distributions'][kind][str(h*2)]={}
  for phase,rows in records.items():
   if not rows:
    out["distributions"][kind][str(h*2)][phase]=dict(configurations=0,median_MAE=None,p90_MAE=None,wins=[0]*4,ties=[0]*4,losses=[0]*4,fraction_beating_baseline=None,rows=[]);continue
   e=np.array([x['model_MAE'] for x in rows]);b=np.array([x['baseline_MAE'] for x in rows]);tol=1e-12+1e-6*abs(b);ties=abs(e-b)<=tol;wins=e<b-tol
   out['distributions'][kind][str(h*2)][phase]=dict(configurations=len(rows),median_MAE=np.median(e,axis=0).tolist(),p90_MAE=np.quantile(e,.9,axis=0).tolist(),wins=wins.sum(0).tolist(),ties=ties.sum(0).tolist(),losses=(~(wins|ties)).sum(0).tolist(),fraction_beating_baseline=wins.mean(0).tolist(),rows=rows)
 pred=np.zeros_like(truth);seen=[]
 for test in tests:
  v=np.load(R/f"data/collected/fold{test['fold']:02}-test-predictions.npz");ids=v['case_indices'];seen.extend(ids.tolist());pred[ids,0]=truth[ids,0];pred[ids,1:]=np.sinh(v['normalized_rollout']*v['std']+v['mean'])*v['physical_scales']
 assert len(seen)==len(set(seen)) and sorted(seen)==sorted(json.loads((R/'schema.json').read_text())['rotations'][0]['test'])
 ids=np.array(seen);truth=truth[ids];pred=pred[ids];tt=a['time'][ids];q=np.maximum(truth[:,:,2],0);pq=np.maximum(pred[:,:,2],0)
 total=np.trapezoid(q,tt,axis=1);ptotal=np.trapezoid(pq,tt,axis=1);tim=np.array([[timing(pq[i],tt[i],f)-timing(q[i],tt[i],f) for f in [.1,.5,.9]] for i in range(len(ids))]);late=[]
 for i in range(len(ids)):
  end=timing(q[i],tt[i],.99)
  if not np.isfinite(end):late.append(np.nan);continue
  t=np.r_[end,tt[i,tt[i]>end]];late.append(max(0,float(np.trapezoid(np.interp(t,tt[i],pq[i])-np.interp(t,tt[i],q[i]),t))))
 def avg(x):return grouped(np.asarray(x),ids).mean(0)
 defined=np.isfinite(tim).all(1);gtime=grouped(abs(tim[defined]),ids[defined]);net=(truth[:,0,:2]-truth[:,-1,:2]);pnet=(pred[:,0,:2]-pred[:,-1,:2]);valid=np.isfinite(late)
 out['events'][kind]=dict(total_release_error_percent=float(100*avg(abs(ptotal-total))/avg(total)),peak_error_percent=float(100*avg(abs(pq.max(1)-q.max(1)))/avg(q.max(1))),timing_defined_histories=int(defined.sum()),timing_undefined_histories=int((~defined).sum()),median_abs_cumulative_t10_t50_t90_error_s=np.median(gtime,axis=0).tolist(),late_excess_kg=float(grouped(np.asarray(late)[valid],ids[valid]).mean()),net_water_fuel_loss_MAE_kg=avg(abs(pnet-net)).tolist(),true_mean_abs_net_loss_kg=avg(abs(net)).tolist(),negative_mean_magnitude=avg(np.maximum(-pred[:,1:],0).mean(1)).tolist(),mass_increase_total_kg=avg(np.maximum(np.diff(pred[:,:,:2],axis=1),0).sum(1)).tolist())
out['scope']='Frozen v1 masks. Each scenario averages eligible forecast origins, seed replicas averaged per physical configuration. Distributions pool eligible physical configurations; one fixed test fold per training size; headline percentages are ratios of grouped means in learning-curve.json. Ties use 1e-12 + 1e-6*baseline MAE. Event timing uses positive gas only, raw states retained for invalidity; undefined timing explicitly counted. No training or test-driven selection.'
(R/'results/scenario-audit.json').write_text(json.dumps(out,indent=2,allow_nan=False));print(json.dumps(out['events'],indent=2))
