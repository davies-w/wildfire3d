"""Check tail-risk arithmetic and frozen TRAIN-only derivatives, without fitting."""
from pathlib import Path
import json,hashlib
import numpy as np
import torch
from joint_decoder import JointDecoder
from joint_objective import objective,weighted_cvar
R=Path(__file__).resolve().parents[1];D=R/'data/joint-decoder-candidate';torch.set_num_threads(4)
v=torch.tensor([0.,1.,2.,3.],requires_grad=True);result=weighted_cvar(v,torch.ones(4),.5);assert float(result.detach())==2.5;result.backward();assert torch.equal(v.grad,torch.tensor([0.,0.,.5,.5]));assert torch.isclose(weighted_cvar(torch.tensor([1.,3.]),torch.tensor([3.,1.]),.5),torch.tensor(2.));assert torch.isclose(weighted_cvar(v.detach(),torch.ones(4),1.),v.detach().mean());assert torch.isclose(weighted_cvar(v.detach().repeat_interleave(2),torch.full((8,),.5),.5),torch.tensor(2.5))
source_hashes={name:hashlib.sha256((R/'model_evaluation'/name).read_bytes()).hexdigest() for name in ['joint_decoder.py','joint_objective.py','validate_joint_objective.py']};(R/'results/joint-objective-preflight.json').write_text(json.dumps(dict(passed=False,status='running',source_hashes=source_hashes))+'\n')
a=np.load(D/'features.npz');p=json.loads((D/'candidate-plan.json').read_text());n=json.loads((D/'base-normalization.json').read_text());ids=p['fit_indices'][:64];x=torch.tensor(a['features'][ids]);base=torch.tensor(a['base_states'][ids]);raw=torch.tensor(a['truth'][ids]);times=torch.tensor(a['time'][ids]);ck=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);std=torch.tensor(n['std']);scales=torch.tensor(n['physical_encoding_scales']);config=a['configuration'];fit=p['fit_indices'];rep=torch.tensor([1/np.count_nonzero(config[fit]==config[i]) for i in ids],dtype=torch.float32);active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5);weights=torch.empty(64,90)
for j in range(64):
 ac=active[j];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);weights[j]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))*rep[j]
reports={}
for mode in ['direct','interval']:
 m=JointDecoder(ck['feature_mean'],ck['feature_std'],std,scales,mode);m.load_state_dict(ck['model']);before={k:v.clone() for k,v in m.state_dict().items()};pred=m(x,base,raw[:,0],times);loss,parts=objective(pred,raw[:,1:],raw[:,0],times,scales,std,weights,rep,raw[:,:,2].abs().amax(1));assert torch.isfinite(loss);loss.backward();assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in m.parameters());assert (m.w2.grad.norm(dim=1)>0).all();assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items());reports[mode]=dict(loss=float(loss.detach()),components={k:float(v.detach()) for k,v in parts.items()},last_layer_gradient_norm_per_head=m.w2.grad.norm(dim=1).tolist(),parameters_unchanged=True)
# Padded future points must not influence a shorter forecast's objective.
valid=torch.zeros(64,90,dtype=torch.bool);valid[:,:16]=True;shortweights=torch.zeros_like(weights);shortweights[:,:16]=rep[:,None]
with torch.no_grad():
 short,_=objective(base[:,:16],raw[:,1:17],raw[:,0],times[:,:17],scales,std,shortweights[:,:16],rep,raw[:,:,2].abs().amax(1))
 padded=base.clone();padded[:,16:]=123.;target=raw[:,1:].clone();target[:,16:]=-42.
 padded_loss,_=objective(padded,target,raw[:,0],times,scales,std,shortweights,rep,raw[:,:,2].abs().amax(1),valid_mask=valid);assert torch.allclose(short,padded_loss,rtol=1e-6,atol=1e-7)
out=dict(padding_future_values_invariant=True,source_hashes=source_hashes,passed=True,fit_partition_only=True,synthetic_weighted_tail_and_gradient_checks=True,replica_weight_split_invariance=True,optimizer_instantiated=False,optimizer_updates=0,modes=reports,scope='Isolated initialization derivatives only; no parameter update, fitted score or selection/confirmation outcome. Tail risk is replica-balanced minibatch CVaR over20%weight mass, not exact configuration-mean p90. State loss balances active/quiet within each sampled forecast. Auxiliary gas/fuel residual matches the TRUE sampling discrepancy instead of forcing it to zero.')
(R/'results/joint-objective-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
