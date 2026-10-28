"""Configuration-balanced descriptive review; no model fitting, selection or new gates."""
import numpy as np

def review(predicted,baseline,truth,hold,configuration,mask):
    predicted,baseline,truth,hold=[np.asarray(x,dtype=np.float64) for x in [predicted,baseline,truth,hold]]
    configuration=np.asarray(configuration);mask=np.asarray(mask,dtype=bool)
    assert predicted.shape==baseline.shape==truth.shape==hold.shape and mask.shape==truth.shape[:2]
    assert all(np.isfinite(x).all() for x in [predicted,baseline,truth,hold])
    count=mask.sum(1);eligible=count>0;rows=[]
    def history_mean(x):return (x*mask[:,:,None]).sum(1)/np.maximum(count[:,None],1)
    values=[history_mean(x) for x in [abs(predicted-truth),abs(baseline-truth),abs(hold-truth),abs(truth)]]
    for c in np.unique(configuration[eligible]):
        keep=eligible&(configuration==c);a,b,n,t=[x[keep].mean(0) for x in values]
        ratio=[float(x/y) if y>0 else None for x,y in zip(a,b)]
        rows.append(dict(configuration=int(c),eligible_histories=int(keep.sum()),eligible_points=int(count[keep].sum()),candidate_MAE=a.tolist(),baseline_MAE=b.tolist(),no_change_MAE=n.tolist(),mean_absolute_truth=t.tolist(),candidate_minus_baseline_MAE=(a-b).tolist(),candidate_over_baseline_MAE=ratio,zero_baseline_error=(b==0).tolist()))
    pooled={key:np.mean([r[key] for r in rows],axis=0).tolist() if rows else None for key in ['candidate_MAE','baseline_MAE','no_change_MAE','mean_absolute_truth']}
    worst={str(state):sorted(rows,key=lambda r:r['candidate_minus_baseline_MAE'][state],reverse=True)[:10] for state in range(4)}
    counts=[dict(configurations=len(rows),candidate_better=sum(r['candidate_minus_baseline_MAE'][j]<0 for r in rows),candidate_worse=sum(r['candidate_minus_baseline_MAE'][j]>0 for r in rows),unchanged=sum(r['candidate_minus_baseline_MAE'][j]==0 for r in rows),zero_baseline_error=sum(r['zero_baseline_error'][j] for r in rows)) for j in range(4)]
    return dict(configurations=rows,pooled=pooled,change_counts_by_state=counts,largest_absolute_MAE_increases_by_state=worst,eligible_points=int(mask.sum()),eligible_histories=int(eligible.sum()))

def phase_masks(labels,h):
    windows=np.lib.stride_tricks.sliding_window_view(labels,h,axis=1);active=np.isin(windows,[1,2]).all(-1);quiet=(windows==0).all(-1);weak=(windows==3).all(-1)
    return dict(overall=np.ones_like(active),active=active,quiet=quiet,weak=weak,transition=~(active|quiet|weak))
