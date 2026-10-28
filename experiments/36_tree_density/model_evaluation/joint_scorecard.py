"""Canonical all-origin horizons over the observed-prefix forecast interface.

Horizon8 is nominal16seconds; horizon16 is nominal32seconds. Actual saved
interval durations are reported. This evaluator does not select models.
"""
import torch
from joint_metrics import groups

@torch.inference_mode()
def horizon_scorecard(predictor,raw,geometry,times,configuration,labels,horizons=(1,4,8,16,45)):
    result={};saved={}
    for h in horizons:
        forecasts=[]
        for origin in range(raw.shape[1]-h):
            forecasts.append(predictor.forecast(raw[:,:origin+1],geometry,times[:,:origin+h+1],h)[:,-1])
        predicted=torch.stack(forecasts,1);truth=raw[:,h:];hold=raw[:,:raw.shape[1]-h];error=(predicted-truth).abs();hold_error=(hold-truth).abs();magnitude=truth.abs();windows=labels.unfold(1,h,1);active=((windows==1)|(windows==2)).all(-1);quiet=(windows==0).all(-1);weak=(windows==3).all(-1);masks=dict(active=active,quiet=quiet,weak=weak,transition=~(active|quiet|weak));phases={}
        for name,mask in masks.items():
            count=mask.sum(1);keep=count>0
            def avg(value):return groups(((value*mask[:,:,None]).sum(1)[keep]/count[keep,None]),configuration[keep]).tolist() if bool(keep.any()) else None
            phases[name]=dict(points=int(mask.sum()),eligible_histories=int(keep.sum()),eligible_configurations=len(torch.unique(configuration[keep])),model_MAE=avg(error),no_change_MAE=avg(hold_error),mean_absolute_truth=avg(magnitude))
        duration=times[:,h:]-times[:,:times.shape[1]-h]
        result[str(h)]=dict(steps=h,nominal_seconds=2*h,actual_duration_min_s=float(duration.min()),actual_duration_max_s=float(duration.max()),finite=bool(torch.isfinite(predicted).all()),model_MAE=groups(error.mean(1),configuration).tolist(),no_change_MAE=groups(hold_error.mean(1),configuration).tolist(),mean_absolute_truth=groups(magnitude.mean(1),configuration).tolist(),phases=phases)
        saved[h]=predicted
    return result,saved
