"""Four-output development scoring and prospectively frozen model selection."""
import torch
from gas_head_metrics import evaluate as legacy_evaluate

def groups(value, config):
    _, inverse, counts = torch.unique(config, return_inverse=True, return_counts=True)
    w = counts[inverse].to(value.dtype).reciprocal()
    return (value*w.reshape((-1,)+(1,)*(value.ndim-1))).sum(0)/len(counts)

@torch.no_grad()
def phase_masks(labels, display):
    # ScorecardV1: every interval label in the forecast window must agree.
    length=labels.shape[1];end=torch.arange(1,length+1,device=labels.device)
    begin=(end-16).clamp_min(0) if display else torch.zeros_like(end)
    def all_window(ok):
        bad=torch.cat([torch.zeros(len(labels),1,device=labels.device,dtype=torch.int64),(~ok).long().cumsum(1)],1)
        return bad[:,end]-bad[:,begin]==0
    active=all_window((labels==1)|(labels==2));quiet=all_window(labels==0);weak=all_window(labels==3)
    masks=dict(active=active,quiet=quiet,weak=weak,transition=~(active|quiet|weak))
    return masks

@torch.no_grad()
def score_prediction(prediction, raw, times, config, labels, scales, std, *, display=False):
    result = legacy_evaluate(prediction[:,:,2],prediction,raw,times,config,labels,scales,std)
    result['histories'] = len(prediction)
    result['configurations'] = len(torch.unique(config))
    errors = (prediction-raw[:,1:]).abs()
    phases = {}
    for name,mask in phase_masks(labels,display).items():
        den=mask.sum(1);keep=den>0
        phases[name]=dict(points=int(mask.sum()),eligible_histories=int(keep.sum()),eligible_configurations=len(torch.unique(config[keep])),physical_MAE=groups((errors*mask[:,:,None]).sum(1)[keep]/den[keep,None],config[keep]).tolist() if bool(keep.any()) else None)
    result['forecast_window_phases']=phases
    above=(prediction[:,:,:2]-raw[:,0,None,:2]).clamp_min(0)
    result['mass_above_origin_mean_kg']=groups(above.mean(1),config).tolist()
    result['trajectory_interpretation']='Stitched forecast revisions; increases are not a single physical trajectory.' if display else 'One uninterrupted forecast from initial state.'
    return result

def checks(b,c,k,scales):
    def better(x,y,f):return x is not None and y is not None and x>0 and y<=x*(1-f)
    def bounded(x,y,f):return x is not None and y is not None and y<=x*(1+f)
    a,z=b['autonomous'],c['autonomous'];d,e=b['display'],c['display'];limit=k['full_autonomous_integral_peak_time_consistency_overprediction_tail_relative_increase_at_most']
    result=dict(display_each_state=all(better(x,y,k['display_each_state_MAE_relative_reduction_at_least']) for x,y in zip(d['physical_MAE_by_feature'],e['physical_MAE_by_feature'])),display_startup=better(d['startup_gas_p90_deficit'],e['startup_gas_p90_deficit'],k['display_startup_gas_p90_relative_reduction_at_least']),display_peak=better(d['peak_release_MAE_kg_s'],e['peak_release_MAE_kg_s'],k['display_gas_peak_amplitude_MAE_relative_reduction_at_least']),display_objective=bounded(d['objective'],e['objective'],k['display_original_objective_relative_increase_at_most']),autonomous_startup=better(a['startup_gas_p90_deficit'],z['startup_gas_p90_deficit'],k['full_autonomous_startup_gas_p90_relative_reduction_at_least']),autonomous_peak=better(a['peak_release_MAE_kg_s'],z['peak_release_MAE_kg_s'],k['full_autonomous_peak_amplitude_MAE_relative_reduction_at_least']),autonomous_objective=bounded(a['objective'],z['objective'],k['full_autonomous_original_objective_relative_increase_at_most']),autonomous_each_state=all(bounded(x,y,k['full_autonomous_each_state_MAE_relative_increase_at_most']) for x,y in zip(a['physical_MAE_by_feature'],z['physical_MAE_by_feature'])),finite=all(r['finite'] for r in [a,z,d,e]))
    for name,field in [('integral','released_fuel_integral_MAE_kg'),('time','peak_time_MAE_s'),('consistency','gas_dry_fuel_consistency_residual_kg'),('overprediction','startup_gas_p90_overprediction')]:result['autonomous_'+name]=bounded(a[field],z[field],limit)
    for regime in ['autonomous','display']:
        x,y=b[regime]['quiet_physical_MAE'],c[regime]['quiet_physical_MAE'];result[regime+'_quiet']=x is not None and y is not None and all((v-u)/s<=k['quiet_state_increase_at_most_in_physical_encoding_scale'] for u,v,s in zip(x,y,scales))
    return result

def guarded(b,c,k,scales):
    ck=checks(b,c,k,scales)
    guards=all(value for name,value in ck.items() if name not in ['display_each_state','display_startup','display_peak','autonomous_startup','autonomous_peak'])
    return guards and all(y<=x*1.05 for x,y in zip(b['display']['physical_MAE_by_feature'],c['display']['physical_MAE_by_feature']))

def rank(b,row):
    ratios=[y/x if x>0 else (0 if y==0 else float('inf')) for x,y in zip(b['display']['physical_MAE_by_feature'],row['metrics']['display']['physical_MAE_by_feature'])]
    return (max(ratios),sum(ratios)/4,row['metrics']['display']['startup_gas_p90_deficit'],row['metrics']['autonomous']['objective'],row['epoch'])

def select(b,rows,k,scales):
    accepted=[r for r in rows if all(checks(b,r['metrics'],k,scales).values())]
    eligible=accepted or [r for r in rows if guarded(b,r['metrics'],k,scales)]
    assert eligible,'Raw-GRU fallback must remain guarded'
    return min(eligible,key=lambda r:rank(b,r)),bool(accepted)

def choose_winner(b,selections):
    eligible=[s for s in selections if s['accepted_on_selection']]
    if not eligible:return 'raw_baseline'
    return min(eligible,key=lambda s:(rank(b,s['row']),0 if s['arm']=='direct' else 1))['arm']
