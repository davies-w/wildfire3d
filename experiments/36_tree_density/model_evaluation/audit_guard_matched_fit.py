"""Fit-only residual/gradient audit and posthoc selection-check census; never update parameters."""
from pathlib import Path
import hashlib,json,sys
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/guard-matched-pilot01';O=R/'data/guard-matched-pilot01-results';sys.path.insert(0,str(D))
from guard_matched_data import GuardMatchedData as ContextData
from joint_decoder import JointDecoder
from guard_matched_objective import objective
from joint_metrics import score_prediction,groups,checks,guarded
load=lambda p:json.loads(p.read_text());assert load(R/'results/guard-matched-pilot01-analysis.json')['passed'];torch.set_num_threads(4);d=ContextData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);snapshot=torch.load(O/'balanced_tail-selected.pt',map_location='cpu',weights_only=False);assert snapshot['apply_decoder'];m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);m.load_state_dict(snapshot['model']);before={k:v.clone() for k,v in m.state_dict().items()};normalization=load(D/'loss-normalization.json');ids=d.roles['fit'];parameters=tuple(p for p in m.parameters() if p.requires_grad)
with torch.inference_mode():
 bfull,bdisplay,bdiag=d.predictions(None,ids);cfull,cdisplay,cdiag=d.predictions(m,ids);args=(d.raw[ids],d.times[ids],d.config[ids],d.labels[ids],d.scales,d.std);baseline={};candidate={};quiet_diagnostics={};quiet=d.labels[ids]==0;count=quiet.sum(1);keep=count>0
 for name,b,c in [('autonomous',bfull,cfull),('display',bdisplay,cdisplay)]:
  baseline[name]=score_prediction(b,*args,display=name=='display');candidate[name]=score_prediction(c,*args,display=name=='display');gap=(c-d.raw[ids,1:]).abs()-(b-d.raw[ids,1:]).abs();tau=.001*d.scales
  avg=lambda value:groups((value*quiet[:,:,None]).sum(1)[keep]/count[keep,None],d.config[ids][keep]).tolist()
  quiet_diagnostics[name]=dict(aggregate_MAE_delta_by_state=avg(gap),fraction_points_worse_by_more_than_slack=avg((gap>tau).float()),mean_pointwise_log_excess_by_state=avg(torch.log1p((gap-tau).clamp_min(0)/tau)),physical_slack=tau.tolist(),eligible_fit_histories=int(keep.sum()))
ratios={name:[y/x for x,y in zip(baseline[name]['physical_MAE_by_feature'],candidate[name]['physical_MAE_by_feature'])] for name in ['autonomous','display']};gradients=[]
for seed in [3640,3641,3642]:
 generator=torch.Generator().manual_seed(seed);batch=ids[torch.randperm(len(ids),generator=generator)[:128]];origins=torch.where(torch.arange(128)%2==0,torch.full((128,),-1),torch.randint(0,75,(128,),generator=generator));args=d.training_batch(m,batch,origins);loss,parts=objective(*args[:4],d.scales,d.std,*args[4:],**d.objective_metadata(batch,origins),normalization=normalization);vectors={}
 for name,term in parts.items():
  g=torch.autograd.grad(term,parameters,retain_graph=True,allow_unused=True);vectors[name]={head:torch.cat([(torch.zeros_like(p) if value is None else value)[head].flatten() for p,value in zip(parameters,g)]) for head in [2,3]}
 def cosine(a,b):
  denominator=a.norm()*b.norm();return float(torch.dot(a,b)/denominator) if denominator>0 else None
 gradients.append(dict(seed=seed,histories=128,physical_gas_vs_under_tail_cosine=cosine(vectors['physical'][2],vectors['under_tail'][2]),physical_gas_vs_quiet_cosine=cosine(vectors['physical'][2],vectors['quiet_nonharm'][2]),physical_heating_vs_quiet_cosine=cosine(vectors['physical'][3],vectors['quiet_nonharm'][3]),gas_gradient_norm_by_component={n:float(v[2].norm()) for n,v in vectors.items()},heating_gradient_norm_by_component={n:float(v[3].norm()) for n,v in vectors.items()},loss=float(loss.detach())))
plan=load(D/'trial-plan.json');selection_base=load(O/'selection-baseline.json');census={}
for arm in plan['arms']:
 rows=[load(O/f'{arm}-epoch{ep:03}.json') for ep in range(10,301,10)];allchecks=[checks(selection_base,r['metrics'],plan['acceptance'],d.scales.tolist()) for r in rows];best=min(rows,key=lambda r:r['metrics']['autonomous']['startup_gas_p90_deficit']);census[arm]=dict(evaluated_epochs=len(rows),guarded_epochs=[r['epoch'] for r in rows if guarded(selection_base,r['metrics'],plan['acceptance'],d.scales.tolist())],failures_by_check={key:sum(not c[key] for c in allchecks) for key in allchecks[0]},best_startup_epoch_posthoc=best['epoch'],best_startup_ratio_posthoc=best['metrics']['autonomous']['startup_gas_p90_deficit']/selection_base['autonomous']['startup_gas_p90_deficit'],best_startup_checks=checks(selection_base,best['metrics'],plan['acceptance'],d.scales.tolist()),minimum_display_MAE_ratio_per_state_potentially_different_epochs=[min(r['metrics']['display']['physical_MAE_by_feature'][j]/selection_base['display']['physical_MAE_by_feature'][j] for r in rows) for j in range(4)])
assert not d.confirmation_open and all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
out=dict(passed=True,optimizer_updates=0,parameters_unchanged=True,arm='balanced_tail',epoch=snapshot['epoch'],fit_histories=len(ids),fit_MAE_ratios=ratios,fit_baseline=baseline,fit_candidate=candidate,quiet_diagnostics=quiet_diagnostics,gradient_audits=gradients,selection_check_census=census,confirmation_and_test_not_used_for_audit=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Posthoc diagnosis only; balanced-tail total additionally weights under_tail0.2 and over_tail0.1; reported gradients are unweighted components. Component minima may belong to different checkpoints and are not a candidate. Pointwise quiet penalty is stronger than the unchanged aggregate guard. Local gradient norms/cosines are not Adam steps, causal proof or an error floor. No optimizer update, new selection, confirmation retuning or deployment.')
(R/'results/guard-matched-fit-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['fit_baseline','fit_candidate']},indent=2))
