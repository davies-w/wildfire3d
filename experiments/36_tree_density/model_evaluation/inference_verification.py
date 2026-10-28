"""Real-prefix paired inference for the complete gallery and canonical evaluation scope."""
import torch
from joint_metrics import score_prediction
from canonical_metrics import score_horizon

@torch.inference_mode()
def evaluate_prefix_pair(predictor,raw,geometry,times,configuration,labels,scales,std):
    assert raw.shape[1:]==(91,4)
    arrays={};constraints=dict(finite=True,mass_nonnegative=True,gas_nonnegative=True,coherent_mass_nonincreasing=True,max_mass_increase_kg=0.,coherent_forecasts=0,forecasts_with_negative_observed_water_boundary=0)
    def observe(prediction,initial):
        curve=torch.cat([initial[:,None,:2].clamp_min(0),prediction[:,:,:2]],1);increase=float((curve[:,1:]-curve[:,:-1]).clamp_min(0).max())
        constraints['finite'] &= bool(torch.isfinite(prediction).all());constraints['mass_nonnegative'] &= bool((prediction[:,:,:2]>=0).all());constraints['gas_nonnegative'] &= bool((prediction[:,:,2]>=0).all());constraints['coherent_mass_nonincreasing'] &= increase<=2e-5;constraints['max_mass_increase_kg']=max(constraints['max_mass_increase_kg'],increase);constraints['coherent_forecasts']+=len(prediction);constraints['forecasts_with_negative_observed_water_boundary']+=int((initial[:,0]<0).sum())
    full,_,base_full=predictor.forecast(raw[:,:1],geometry,times,90,return_features=True);observe(full,raw[:,0]);arrays['candidate_autonomous']=full;arrays['baseline_autonomous']=base_full
    rolling=[];base_rolling=[]
    for origin in range(75):
        pred,_,base=predictor.forecast(raw[:,:origin+1],geometry,times[:,:origin+17],16,return_features=True);observe(pred,raw[:,origin]);rolling.append(pred[:,-1]);base_rolling.append(base[:,-1])
    rolling=torch.stack(rolling,1);base_rolling=torch.stack(base_rolling,1);arrays['candidate_display']=torch.cat([full[:,:15],rolling],1);arrays['baseline_display']=torch.cat([base_full[:,:15],base_rolling],1)
    args=(raw,times,configuration,labels,scales,std);report={}
    for name in ['baseline','candidate']:
        report[name]=dict(autonomous=score_prediction(arrays[name+'_autonomous'],*args),display=score_prediction(arrays[name+'_display'],*args,display=True),canonical={})
    hold_full=raw[:,:1].expand(-1,90,-1);hold_display=torch.cat([hold_full[:,:15],raw[:,:75]],1);report['no_change']=dict(autonomous=score_prediction(hold_full,*args),display=score_prediction(hold_display,*args,display=True),canonical={})
    for h in [1,4,8,16,45]:
        if h==16:predicted,baseline=rolling,base_rolling
        else:
            predicted=[];baseline=[]
            for origin in range(91-h):
                pred,_,base=predictor.forecast(raw[:,:origin+1],geometry,times[:,:origin+h+1],h,return_features=True);observe(pred,raw[:,origin]);predicted.append(pred[:,-1]);baseline.append(base[:,-1])
            predicted=torch.stack(predicted,1);baseline=torch.stack(baseline,1)
        for name,pred in [('candidate',predicted),('baseline',baseline),('no_change',raw[:,:91-h])]:report[name]['canonical'][str(h)]=score_horizon(pred,raw,times,configuration,labels,h)
        arrays['candidate_h'+str(h)]=predicted;arrays['baseline_h'+str(h)]=baseline
    assert constraints['coherent_forecasts']==382*len(raw)
    report['constraints']=constraints;report['trajectory_interpretation']='Constraints apply to each coherent forecast separately, with projected nonnegative observed mass boundary. Stitched display jumps are forecast revisions. Heating stays signed; no energy/temperature claim.'
    return report,arrays
