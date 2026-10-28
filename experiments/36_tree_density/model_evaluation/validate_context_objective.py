"""Fit-only physical-objective arithmetic, role, context and gradient preflight."""
from pathlib import Path
import hashlib,json
import torch
from context_data import ContextData
from context_decoder import JointDecoder
from context_objective import objective
R=Path(__file__).resolve().parents[1];C=R/'data/joint-decoder-candidate';D=R/'data/context-candidate';torch.set_num_threads(4);d=ContextData(C,rolling_root=R/'data/joint-rolling-features');ck=torch.load(D/'initial-context.pt',map_location='cpu',weights_only=False);normalization=json.loads((D/'loss-normalization.json').read_text());ids=d.roles['fit'][:8]
def model(mode='interval'):
 m=JointDecoder(ck['feature_mean'],ck['feature_std'],d.std,d.scales,mode,ck['state_mean']);m.load_state_dict(ck['model']);return m
(R/'results/context-objective-preflight.json').write_text(json.dumps(dict(passed=False,status='running'))+'\n')
reports=[]
for origins in [torch.tensor([-1,0,-1,16,-1,74,-1,8]),torch.full((8,),-1),torch.full((8,),74)]:
 m=model();before={k:v.clone() for k,v in m.state_dict().items()};a=d.training_batch(m,ids,origins);metadata=d.objective_metadata(ids,origins);loss,parts=objective(*a[:4],d.scales,d.std,*a[4:],**metadata,normalization=normalization);assert torch.isfinite(loss);loss.backward();assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in m.parameters());assert (m.w2.grad.norm(dim=1)>0).all();assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
 with torch.no_grad():
  changed=[v.clone() if torch.is_tensor(v) else v for v in a];invalid=~a[-1];changed[0][invalid]=123.;changed[1][invalid]=-42.;meta2={k:v.clone() for k,v in metadata.items()};meta2['base'][invalid]=-99.;meta2['labels'][invalid]=0;other,_=objective(*changed[:4],d.scales,d.std,*changed[4:],**meta2,normalization=normalization);assert torch.allclose(loss,other,rtol=1e-6,atol=1e-7)
 reports.append(dict(origins=origins.tolist(),loss=float(loss.detach()),parts={k:float(v.detach()) for k,v in parts.items()},all_four_head_gradients_nonzero=True,padding_invariant=True))
for role in ['selection','confirmation']:
 try:d.objective_metadata(d.roles[role][:1],torch.tensor([-1]));raise RuntimeError('Role guard failed')
 except AssertionError:pass
# Isolate explicit lead/origin dependence with a nonzero untrained probe; no fit.
m=model('direct');torch.manual_seed(3631)
with torch.no_grad():
 m.w2.normal_(std=.05);features=d.x[ids[:1],:16];base=d.base[ids[:1],:16];initial=d.raw[ids[:1],0];times=d.times[ids[:1],:17];a=m(features,base,initial,times);shifted=times.clone();shifted[:,0]-=2;b=m(features,base,initial,shifted);assert not torch.equal(a,b);c=m(features,base,initial+torch.tensor([.1,.1,0.,0.]),times);assert not torch.equal(a,c)
 # Prefix outputs stay invariant when a later forecast continuation is omitted.
 full=m(d.x[ids[:1]],d.base[ids[:1]],initial,d.times[ids[:1]]);assert torch.allclose(full[:,:16],a,rtol=1e-5,atol=2e-5)
# Actual objective call verifies mixed-regime weights and endpoint-only physical loss.
pred=torch.ones(2,90,4);truth=torch.zeros_like(pred);init=torch.zeros(2,4);times=torch.arange(91)[None].expand(2,-1).float()*2;valid=torch.ones(2,90,dtype=torch.bool);valid[1,16:]=False;weights=valid.float();labels=torch.ones(2,90,dtype=torch.long);full=torch.tensor([True,False]);norm=dict(autonomous_MAE=[1.]*4,display_MAE=[1.]*4,autonomous_objective=1.,display_objective=1.)
_,parts=objective(pred,truth,init,times,torch.ones(4),torch.ones(4),weights,torch.ones(2),torch.ones(2),valid,base=pred,labels=labels,full=full,normalization=norm);assert parts['physical']==1 and parts['quiet_nonharm']==0 and parts['encoded_nonharm']==0
changed=pred.clone();changed[1,:15]*=3
_,parts2=objective(changed,truth,init,times,torch.ones(4),torch.ones(4),weights,torch.ones(2),torch.ones(2),valid,base=changed,labels=labels,full=full,normalization=norm);assert parts2['physical']==parts['physical']
labels[1,15]=0
_,parts3=objective(pred,truth,init,times,torch.ones(4),torch.ones(4),weights,torch.ones(2),torch.ones(2),valid,base=torch.zeros_like(pred),labels=labels,full=full,normalization=norm);assert parts3['quiet_nonharm']>0
proof=dict(passed=True,optimizer_updates=0,parameters_unchanged_during_derivative_checks=True,fit_only=True,confirmation_closed=not d.confirmation_open,explicit_lead_and_observed_origin_influence_probe=True,prefix_invariant=True,physical_sampling_weights_sum_to_one=True,cases=reports,source_hashes={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['context_decoder.py','context_data.py','context_objective.py','validate_context_objective.py']},scope='Untrained CPU checks and isolated derivatives only. Nonzero probes are random parameters, not optimizer updates or accuracy evidence. Quiet penalty is pointwise/soft and does not prove aggregate guards. CUDA restoration/timing and complete scientific evaluation remain required.')
(R/'results/context-objective-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
