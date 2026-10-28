"""Canonical endpoint scoring plus additive guards; original acceptance checks remain intact."""
import torch
from joint_metrics import groups,checks as legacy_checks,guarded as legacy_guarded,rank
CANONICAL_LIMIT=.05

def score_horizon(predicted,raw,times,configuration,labels,h):
    assert predicted.shape==(len(raw),91-h,4)
    truth=raw[:,h:];hold=raw[:,:91-h];error=(predicted-truth).abs();hold_error=(hold-truth).abs();magnitude=truth.abs();windows=labels.unfold(1,h,1)
    active=((windows==1)|(windows==2)).all(-1);quiet=(windows==0).all(-1);weak=(windows==3).all(-1);masks=dict(active=active,quiet=quiet,weak=weak,transition=~(active|quiet|weak));phases={}
    for name,mask in masks.items():
        count=mask.sum(1);keep=count>0
        def avg(value):return groups((value*mask[:,:,None]).sum(1)[keep]/count[keep,None],configuration[keep]).tolist() if bool(keep.any()) else None
        phases[name]=dict(points=int(mask.sum()),eligible_histories=int(keep.sum()),eligible_configurations=len(torch.unique(configuration[keep])),model_MAE=avg(error),no_change_MAE=avg(hold_error),mean_absolute_truth=avg(magnitude))
    duration=times[:,h:]-times[:,:91-h]
    return dict(steps=h,nominal_seconds=2*h,actual_duration_min_s=float(duration.min()),actual_duration_max_s=float(duration.max()),finite=bool(torch.isfinite(predicted).all()),model_MAE=groups(error.mean(1),configuration).tolist(),no_change_MAE=groups(hold_error.mean(1),configuration).tolist(),mean_absolute_truth=groups(magnitude.mean(1),configuration).tolist(),phases=phases)

def canonical_checks(b,c):
    result={}
    for h in ['1','4','8','16','45']:
        for state,(old,new) in enumerate(zip(b[h]['model_MAE'],c[h]['model_MAE'])):
            result[f'canonical_h{h}_state{state}']=old is not None and new is not None and new<=old*(1+CANONICAL_LIMIT)
        result[f'canonical_h{h}_finite']=b[h]['finite'] and c[h]['finite']
    return result

def checks(b,c,k,scales):return {**legacy_checks(b,c,k,scales),**canonical_checks(b['canonical'],c['canonical'])}

def guarded(b,c,k,scales):return legacy_guarded(b,c,k,scales) and all(canonical_checks(b['canonical'],c['canonical']).values())

def select(b,rows,k,scales):
    accepted=[r for r in rows if all(checks(b,r['metrics'],k,scales).values())]
    eligible=accepted or [r for r in rows if guarded(b,r['metrics'],k,scales)]
    assert eligible,'Raw fallback must remain guarded'
    return min(eligible,key=lambda r:rank(b,r)),bool(accepted)
