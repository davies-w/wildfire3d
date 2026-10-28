"""Offline evaluator/data/selection checks. No optimizer or confirmation scores."""
from pathlib import Path
import copy,hashlib,json
import torch,numpy as np
from joint_data import JointData
from joint_decoder_v2 import JointDecoder
from joint_objective_v2 import objective
from joint_metrics import phase_masks,checks,guarded,select,choose_winner
R=Path(__file__).resolve().parents[1];C=R/'data/joint-decoder-candidate';torch.set_num_threads(4);source_names=['joint_data.py','joint_metrics.py','joint_decoder_v2.py','joint_objective_v2.py','validate_joint_pipeline_v2.py'];hashes={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in source_names};outpath=R/'results/joint-pipeline-v2-preflight.json';outpath.write_text(json.dumps(dict(passed=False,status='running',source_hashes=hashes))+'\n');d=JointData(C,rolling_root=R/'data/joint-rolling-features');plan=json.loads((R/'results/joint-decoder-trial-plan.json').read_text());ck=torch.load(C/'initial-decoder.pt',map_location='cpu',weights_only=False)
def model(mode):
 m=JointDecoder(ck['feature_mean'],ck['feature_std'],d.std,d.scales,mode);m.load_state_dict(ck['model']);return m
# Replay known TRAIN baseline; confirmation is never opened here.
ids=torch.cat([d.roles['fit'],d.roles['selection']]);baseline=d.score(None,ids);old=json.loads((R/'results/exposure-pilot02-analysis.json').read_text())['arms'][0]['gpu_row']['train']['rollout']
for key in ['objective','physical_MAE_by_feature','peak_release_MAE_kg_s','peak_time_MAE_s','released_fuel_integral_MAE_kg']:assert np.allclose(baseline['autonomous'][key],old[key],rtol=.002,atol=1e-7),(key,baseline['autonomous'][key],old[key])
selection_baseline=d.score(None,d.roles['selection']);assert guarded(selection_baseline,selection_baseline,plan['acceptance'],d.scales.tolist())
small=d.roles['fit'][:8];a,b,_=d.predictions(None,small);x,y,_=d.predictions(model('direct'),small);assert torch.equal(a,x) and torch.equal(b,y);assert torch.equal(b[:,:15],d.base[small,:15]) and torch.equal(b[:,15:],d.rb[small,:,-1])
for role in ['selection','confirmation']:
 try:d.training_batch(model('direct'),d.roles[role][:1],torch.tensor([-1]));raise RuntimeError('Role guard failed')
 except AssertionError:pass
try:d.score(None,d.roles['confirmation'][:1]);raise RuntimeError('Confirmation guard failed')
except AssertionError:pass
labels=torch.tensor([[1,2,1,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3],[0]*18,[3]*18])
for display in [False,True]:
 masks=phase_masks(labels,display)
 for target in range(18):
  w=labels[:,max(0,target-15) if display and target>=15 else 0:target+1];active=torch.isin(w,torch.tensor([1,2])).all(1);quiet=(w==0).all(1);weak=(w==3).all(1)
  for name,expected in [('active',active),('quiet',quiet),('weak',weak),('transition',~(active|quiet|weak))]:assert torch.equal(masks[name][:,target],expected)
# Mixed and single-regime derivative checks use fit histories only.
for mode in ['direct','interval']:
 for origins in [torch.tensor([-1,0,-1,16,-1,74,-1,8]),torch.full((8,),-1),torch.full((8,),74)]:
  m=model(mode);before={k:v.clone() for k,v in m.state_dict().items()};args=d.training_batch(m,small,origins);loss,_=objective(args[0],args[1],args[2],args[3],d.scales,d.std,*args[4:]);assert torch.isfinite(loss);loss.backward();assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in m.parameters());assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
# Synthetic metric perturbations verify every threshold and deterministic ranking.
b=baseline;k=plan['acceptance'];scales=d.scales.tolist();assert guarded(b,b,k,scales) and not all(checks(b,b,k,scales).values());good=copy.deepcopy(b)
for regime in ['autonomous','display']:
 r=good[regime]
 for key in ['physical_MAE_by_feature','quiet_physical_MAE']:r[key]=[x*.8 for x in r[key]]
 for key in ['objective','peak_release_MAE_kg_s','peak_time_MAE_s','released_fuel_integral_MAE_kg','gas_dry_fuel_consistency_residual_kg','startup_gas_p90_deficit','startup_gas_p90_overprediction']:r[key]*=.8
assert all(checks(b,good,k,scales).values());fallback=dict(epoch=-1,metrics=b);passing=dict(epoch=20,metrics=good);selected,accepted=select(b,[fallback,passing],k,scales);assert selected==passing and accepted
for key in ['objective','peak_time_MAE_s','released_fuel_integral_MAE_kg','gas_dry_fuel_consistency_residual_kg','startup_gas_p90_overprediction']:
 bad=copy.deepcopy(good);bad['autonomous'][key]=b['autonomous'][key]*1.06;assert not guarded(b,bad,k,scales)
for regime in ['autonomous','display']:
 bad=copy.deepcopy(good);bad[regime]['physical_MAE_by_feature'][0]=b[regime]['physical_MAE_by_feature'][0]*1.06;assert not guarded(b,bad,k,scales)
 bad=copy.deepcopy(good);bad[regime]['quiet_physical_MAE'][2]=b[regime]['quiet_physical_MAE'][2]+scales[2]*.0011;assert not guarded(b,bad,k,scales)
 bad=copy.deepcopy(good);bad[regime]['finite']=False;assert not guarded(b,bad,k,scales)
partial=copy.deepcopy(good);partial['display']['physical_MAE_by_feature'][0]=b['display']['physical_MAE_by_feature'][0]*.95;exploratory=dict(epoch=10,metrics=partial);row,ok=select(b,[fallback,exploratory],k,scales);assert row==exploratory and not ok
selections=[dict(arm=arm,row=passing,accepted_on_selection=True) for arm in ['interval','direct']];assert choose_winner(b,selections)=='direct';assert choose_winner(b,[dict(arm='direct',row=fallback,accepted_on_selection=False)])=='raw_baseline'
result=dict(passed=True,source_hashes=hashes,baseline_TRAIN_metric_replay_close=True,exact_display_assembly=True,direct_initial_both_regimes_bitwise_equal=True,fit_role_only_gradients=True,confirmation_closed=True,scorecard_phase_reference_exact=True,mixed_horizon_derivatives_finite=True,synthetic_selection_acceptance_checks=True,parameters_unchanged=True,optimizer_updates=0,scope='Already examined TRAIN baseline and fit-only initialization derivatives. Confirmation metrics were never opened. No fitted model, test score, CUDA optimizer or accuracy improvement.')
outpath.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
