"""Verify full training-only coverage; pack target arrays and diagnose geometry."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from extract_training import code_hash
R=Path(__file__).resolve().parent;repo=R.parents[1];D=R/'data';out=D/'training-summary';out.mkdir(exist_ok=True)
plan=json.loads((D/'training-plan.json').read_text());schema=json.loads((repo/'experiments/36_tree_density/learning-schema.json').read_text());rot=schema['rotations'][0]
assert hashlib.sha256((repo/'experiments/36_tree_density/learning-schema.json').read_bytes()).hexdigest()==plan['schema_sha256']
expected_ids=rot['train'];assert expected_ids==[x['case_index'] for x in plan['cases']] and len(expected_ids)==1662
paths=list((D/'training-histories').glob('*.json'));assert {p.stem for p in paths}=={x['case'] for x in plan['cases']},'Incomplete or extra histories'
keys=['pivot_height_m','tilt_from_vertical_deg','length_m','end_radius_m','peak_temperature_C']
parameters=np.full((1662,91,5),np.nan,dtype='float32');times=np.empty((1662,91),dtype='float32');active=np.zeros((1662,91),bool)
metric_keys=['hot_recall','hot_precision','iou'];cm=np.full((1662,91,3),np.nan);om=np.full_like(cm,np.nan);om95=np.full_like(cm,np.nan)
records=[];all_active=[];rows_by_config={};jumps=[];input_sha=hashlib.sha256();history_sha=hashlib.sha256();max_time_gap=0.
with np.load(repo/'experiments/36_tree_density/data/learning/sequences.npz') as seq:reference_times=seq['time'][expected_ids]
for i,it in enumerate(plan['cases']):
    p=D/'training-histories'/(it['case']+'.json');b=p.read_bytes();r=json.loads(b)
    assert r['case_index']==expected_ids[i] and r['split']=='train' and r['rotation']==0 and r['fold'] not in [rot['test_fold'],rot['validation_fold']]
    assert r['source_sha256']==it['sha256'] and r['recipe_sha256']==code_hash();assert len(r['snapshots'])==91
    input_sha.update((it['case']+it['sha256']).encode());history_sha.update((it['case']+hashlib.sha256(b).hexdigest()).encode())
    local=[]
    for j,row in enumerate(r['snapshots']):
        times[i,j]=row['time_s'];active[i,j]=row['active']
        if not row['active']:assert row['cone'] is None;continue
        assert list(row['cone'])==keys;v=list(row['cone'].values());assert np.isfinite(v).all();parameters[i,j]=v
        assert 0<=v[1]<=90 and v[2]>0 and v[3]>=0 and v[4]<=row['domain_peak_temperature_C']+1e-8
        for name,dest in [('cone_metrics',cm),('ovoid_metrics',om),('ovoid95_metrics',om95)]:
            m=row[name];assert m['covered_hot_cells']+m['missed_hot_cells']==m['hot_cells'];assert m['covered_hot_cells']+m['cool_cells_included']==m['enclosed_cells'];dest[i,j]=[m[k] for k in metric_keys];assert np.all((dest[i,j]>=0)&(dest[i,j]<=1))
        assert cm[i,j,0]>=.95-1e-9 and om95[i,j,0]>=.95-1e-9
        local.append(row);all_active.append(row)
    assert np.allclose(times[i],reference_times[i],rtol=0,atol=1e-5)
    max_time_gap=max(max_time_gap,float(np.max(abs(times[i]-reference_times[i]))))
    cfg=tuple(it['physical_key']);rows_by_config.setdefault(cfg,[]).append(np.nanmean(cm[i],axis=0) if local else np.full(3,np.nan))
    records.append(dict(case=it['case'],case_index=it['case_index'],physical_key=it['physical_key'],fold=it['fold'],active_frames=len(local),history_sha256=hashlib.sha256(b).hexdigest(),source_sha256=it['sha256']))

valid=active;post=active&(times>=20)
# Explicit indexing avoids confusing history/frame axes.
def medians(mask):
    return {name:{k:float(np.nanmedian(arr[:,:,idx][mask])) for idx,k in enumerate(metric_keys)} for name,arr in [('cone',cm),('ovoid2sigma',om),('ovoid95',om95)]}
paired=active[:,1:]&active[:,:-1];diff=abs(np.diff(parameters,axis=1));distribution={}
for k,name in enumerate(keys):
    distribution[name]=dict(active_percentiles=dict(zip(['min','p50','p95','p99','max'],[float(x) for x in np.percentile(parameters[:,:,k][active],[0,50,95,99,100])])),adjacent_active_absolute_change_percentiles=dict(zip(['p50','p95','p99','max'],[float(x) for x in np.percentile(diff[:,:,k][paired],[50,95,99,100])])) )
config_means=np.array([np.nanmean(v,axis=0) for v in rows_by_config.values() if np.isfinite(v).any()]);equalconfig=np.mean(config_means,axis=0)
proof=dict(passed=True,rotation=0,training_histories=1662,frames=int(active.size),active_frames=int(active.sum()),inactive_frames=int((~active).sum()),validation_histories=0,test_histories=0,exact_case_ids=True,exact_frozen_times_within_1e_5_s=True,max_timestamp_difference_s=max_time_gap,all_source_sha256_verified=True,recipe_sha256=code_hash(),input_manifest_sha256=input_sha.hexdigest(),history_manifest_sha256=history_sha.hexdigest(),case_indices=expected_ids)
summary=dict(training_histories=1662,frames=int(active.size),active_frames=int(active.sum()),inactive_frames=int((~active).sum()),entirely_inactive_histories=int((~active.any(axis=1)).sum()),activity_transitions=int((active[:,1:]!=active[:,:-1]).sum()),configurations_with_active_frames=len(config_means),equal_configuration_weighting='Mean over active frames per history, then histories per physical configuration, then configurations with active frames; inactive frames have no geometric score.',physical_configurations=len(rows_by_config),active_frame_medians=medians(active),after_igniter_frame_medians=medians(post),equal_configuration_mean_cone_scores=dict(zip(metric_keys,[float(x) for x in equalconfig])),ground_apex_fraction=float(np.mean([r['apex_below_crown'] for r in all_active])),domain_peak_missed_frames=sum(r['peak_temperature_missed_C']>1e-6 for r in all_active),frames_with_hot_gas_at_domain_boundary=sum(r['hot_cells_on_domain_boundary']>0 for r in all_active),parameter_diagnostics=distribution,min_saved_step_s=float(np.diff(times).min()),max_saved_step_s=float(np.diff(times).max()),sources=plan['sources'],fit_target_hot_coverage=.95,hot_threshold_C=50,loss_function_selected=False,scope='Geometric extraction on all rotation0 TRAIN histories only. No fitting of a neural model, no validation/test histories, no new simulation. Snapshot temperature maxima are not interval maxima; 50C is not ignition. Cone dimensions can extend outside observed domain. Parameter jumps may reflect constrained geometric fit rather than physical changes.')
np.savez_compressed(out/'targets.npz',case_indices=np.array(expected_ids),time=times,parameters=parameters,active=active,cone_metrics=cm.astype('float32'),ovoid2sigma_metrics=om.astype('float32'),ovoid95_metrics=om95.astype('float32'))
for name,obj in [('summary',summary),('validation',proof),('histories',records),('parameter-schema',dict(parameter_names=keys,units=['m','degrees from vertical','m','m','degC'],inactive='active=false; all five parameters NaN; do not regress inactive NaNs',metric_names=metric_keys,time='instantaneous saved frame',axis='downwind +x and vertical z',apex_xy_m=[8,8],coverage='95% of >50C cell centres',density='no within-cone temperature profile'))]:
    (out/(name+'.json')).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
fig,axs=plt.subplots(2,3,figsize=(14,8))
for k,ax in enumerate(axs.flat[:5]):
    values=parameters[:,:,k][active];hi=np.percentile(values,99);ax.hist(values,bins=45,range=(values.min(),max(float(hi),float(values.min())+1)),color='#237d92');ax.set_title(keys[k]);ax.set_ylabel('Active frames');ax.set_xlabel('Display range through 99th percentile; maxima in JSON')
ax=axs.flat[5];ax.hist(cm[:,:,1][active],bins=30,alpha=.6,label='Cone');ax.hist(om95[:,:,1][active],bins=30,alpha=.6,label='Ovoid 95%');ax.set_title('Fraction of enclosed cells above 50°C');ax.legend()
fig.suptitle('All 1,662 rotation-0 training histories — derived cone parameters, not learned predictions');fig.tight_layout();fig.savefig(out/'distributions.png',dpi=130);plt.close(fig)
print(json.dumps({k:v for k,v in summary.items() if k!='parameter_diagnostics'},indent=2))
