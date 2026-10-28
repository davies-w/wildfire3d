"""Independent guard-estimator fixtures and fit-only derivatives; no optimizer."""
from pathlib import Path
import hashlib,json
import torch
from guard_matched_objective import quiet_aggregate_penalty,objective
from guard_matched_data import GuardMatchedData
from context_data import ContextData
from context_objective import objective as old_objective
from joint_metrics import groups
from timing_decoder import JointDecoder
R=Path(__file__).resolve().parents[1];torch.set_num_threads(4);scale=torch.tensor([1.,1.,.01,100.])
labels=torch.ones(3,90,dtype=torch.long);labels[0,:10]=0;labels[0,50:80]=0;labels[1]=0;q=(labels==0).sum(1).float();weights=torch.tensor([.5,.5,0.]);config=torch.tensor([7,7,9]);base=torch.ones(3,90,4);truth=torch.zeros_like(base);valid=torch.ones(3,90,dtype=torch.bool)
fgap=torch.linspace(-.2,.3,90)[None,:,None].expand(3,-1,4).clone();fgap[1]*=-.5;rgap=torch.linspace(.15,-.12,75)[None,:,None].expand(3,-1,4).clone();rgap[1]*=-.75
_,full_est=quiet_aggregate_penalty(base+fgap,truth,base,labels,torch.ones(3,dtype=torch.bool),valid,scale,q,weights,3.)
rolling=[]
for origin in range(75):
 p=base+rgap[:,origin:origin+1].expand(-1,90,-1);lab=torch.full_like(labels,-1);lab[:,:16]=labels[:,origin:origin+16];mask=torch.arange(90)[None].expand(3,-1)<16
 _,est=quiet_aggregate_penalty(p,truth,base,lab,torch.zeros(3,dtype=torch.bool),mask,scale,q,weights,3.);rolling.append(est)
 # Invalid padded values must not affect the estimator.
 p2=p.clone();p2[:,16:]+=1000;_,e2=quiet_aggregate_penalty(p2,truth,base,lab,torch.zeros(3,dtype=torch.bool),mask,scale,q,weights,3.)
 assert all(torch.equal(est[k],e2[k]) for k in est)
keep=q>0;quiet=labels==0
for name,gap in [('autonomous',fgap),('display',torch.cat([fgap[:,:15],rgap],1))]:
 expected=groups((gap*quiet[:,:,None]).sum(1)[keep]/q[keep,None],config[keep]);actual=.5*full_est[name]+.5*torch.stack([e[name] for e in rolling]).mean(0)
 assert torch.allclose(actual,expected,rtol=1e-5,atol=1e-6),(name,actual,expected)
# A compensating quiet improvement is penalized pointwise despite an inactive aggregate guard.
p=torch.full((1,90,4),2.2);p[:,:30]=1.4;p.requires_grad_();t=torch.zeros_like(p);b=torch.full_like(p,2.);lab=torch.zeros(1,90,dtype=torch.long)
loss,est=quiet_aggregate_penalty(p,t,b,lab,torch.ones(1,dtype=torch.bool),torch.ones(1,90,dtype=torch.bool),scale,torch.tensor([90.]),torch.ones(1),1.)
assert float(loss.detach())==0 and all(bool((v<=.001*scale).all()) for v in est.values());assert torch.count_nonzero(torch.autograd.grad(loss,p)[0])==0
old_point=torch.log1p((((p-t).abs()-(b-t).abs()-.001*scale).clamp_min(0)/(.001*scale)))
assert float(old_point[:,:,3].mean().detach())>0
D=R/'data/timing-decoder-pilot06';data=GuardMatchedData(D);fit=data.roles['fit'];assert data.quiet_fit_configurations==510;assert torch.count_nonzero(data.quiet_count[~data.fit_allowed])==0 and torch.count_nonzero(data.quiet_replica_weight[~data.fit_allowed])==0
assert GuardMatchedData.training_batch is ContextData.training_batch and GuardMatchedData.predictions is ContextData.predictions
initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);model=JointDecoder(initial['feature_mean'],initial['feature_std'],data.std,data.scales,'interval',initial['state_mean']);model.load_state_dict(initial['model']);before={k:v.clone() for k,v in model.state_dict().items()};normalization=json.loads((D/'loss-normalization.json').read_text());ids=fit[:8];origins=torch.tensor([-1,0,16,-1,74,-1,8,-1]);ordered=torch.cat([ids[origins<0],ids[origins>=0]])
metadata=data.objective_metadata(ids,origins);assert torch.equal(metadata['quiet_count'],data.quiet_count[ordered]) and torch.equal(metadata['quiet_replica_weight'],data.quiet_replica_weight[ordered])
for under,over in [(.1,.05),(.3,.15)]:
 model.zero_grad(set_to_none=True);args=data.training_batch(model,ids,origins);new,parts=objective(*args[:4],data.scales,data.std,*args[4:],**metadata,normalization=normalization);_,old=old_objective(*args[:4],data.scales,data.std,*args[4:],**{k:metadata[k] for k in ['base','labels','full']},normalization=normalization)
 assert all(torch.equal(parts[k],old[k]) for k in old if k!='quiet_nonharm')
 total=new+(under-.1)*parts['under_tail']+(over-.05)*parts['over_tail'];assert torch.isfinite(total);total.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters() if p.requires_grad);assert all(p.grad is None for p in model.parameters() if not p.requires_grad)
assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items()) and not data.confirmation_open
proof=dict(passed=True,optimizer_updates=0,weighted_duplicate_empty_quiet_full_and_all75origins_estimates_match_exact_guards=True,padding_invariant=True,compensating_heating_improvement_old_penalty_positive_new_penalty_zero=True,fit_only_metadata_and_row_order_verified=True,forecast_methods_unchanged=True,unchanged_other_loss_components_exact=True,both_arm_derivatives_finite=True,parameters_unchanged=True,fit_histories=len(fit),quiet_eligible_fit_histories=int((data.quiet_count[fit]>0).sum()),quiet_eligible_fit_configurations=data.quiet_fit_configurations,source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['guard_matched_data.py','guard_matched_objective.py','validate_guard_matched_objective.py','context_data.py','context_objective.py']},scope='Loss alignment and derivative checks only. Linear estimator is unbiased before hinge/log; minibatch nonlinear loss is not. No CPU optimizer, CUDA proof, model selection, confirmation/test use or improvement claim.')
(R/'results/guard-matched-objective-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
