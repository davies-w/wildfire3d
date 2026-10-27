"""Prepare a minimal train-only exposure correction; no optimizer or cloud launch."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1]
HELPER='''def exposure_target_factors(weights,train,h):
 # Counts of full-horizon windows containing each transition.
 length=weights.shape[1]
 assert 1<=h<=length
 counts=torch.zeros(length,dtype=weights.dtype,device=weights.device)
 for origin in range(length-h+1):counts[origin:origin+h]+=1
 # Preserve the original total TRAIN loss coefficient, not just raw window count.
 train_weights=weights[train]
 scale=(train_weights*counts).sum()/train_weights.sum()
 return scale/counts
'''
def main():
 source=R/'data/pair-sequence/rotation0';D=R/'data/exposure-candidate';D.mkdir(exist_ok=True)
 worker=(source/'worker.py').read_text();needle='def training_objective(pred,target):return (pred-target).square().sum(-1)/3\n';assert worker.count(needle)==1;worker=worker.replace(needle,needle+HELPER)
 needle="windows=[(int(n),j) for n in train.tolist() for j in range(0,91-h)];order=";assert worker.count(needle)==1;worker=worker.replace(needle,"target_factors=exposure_target_factors(weights,train,h);"+needle)
 needle='state_loss*weights[ids,jj]*keep';assert worker.count(needle)==1;worker=worker.replace(needle,'state_loss*weights[ids,jj]*target_factors[jj]*keep')
 (D/'worker.py').write_text(worker);(D/'model.py').write_bytes((source/'model.py').read_bytes());compile(worker,str(D/'worker.py'),'exec')
 # Execute only the isolated helper, not the worker entrypoint (which launches training).
 import torch
 ns={'torch':torch};exec(HELPER,ns);rng=np.random.default_rng(271027);tests=[]
 for length in [8,90]:
  for h in sorted(set([1,min(8,length),min(16,length),min(32,length),length])):
   w=torch.tensor(rng.uniform(.1,8,(7,length)),dtype=torch.float64);ids=torch.tensor([0,2,4,6]);fac=ns['exposure_target_factors'](w,ids,h);count=torch.zeros(length,dtype=torch.float64)
   for origin in range(length-h+1):count[origin:origin+h]+=1
   old=w[ids]*count;new=old*fac;expected=w[ids]*((w[ids]*count).sum()/w[ids].sum());assert torch.allclose(new,expected,atol=1e-12,rtol=1e-12);assert torch.allclose(old.sum(),new.sum(),atol=1e-10,rtol=1e-12)
   changed=w.clone();changed[[1,3,5]]*=100000;assert torch.equal(fac,ns['exposure_target_factors'](changed,ids,h));assert bool(torch.isfinite(fac).all())
   if h==1:assert torch.allclose(fac,torch.ones_like(fac))
   # Weighted scalar loss gradients have exactly the same coefficient cancellation.
   p=torch.randn(7,length,dtype=torch.float64,requires_grad=True);loss=(p[ids].square()*new).sum();grad=torch.autograd.grad(loss,p)[0];expected_grad=torch.zeros_like(p);expected_grad[ids]=2*p.detach()[ids]*expected;assert torch.allclose(grad,expected_grad,atol=1e-10,rtol=1e-12)
   tests.append(dict(length=length,horizon=h,coefficient_and_gradient_cancellation=True,total_coefficient_preserved=True,heldout_perturbation_invariant=True))
 proof={'passed':True,'source_worker_sha256':hashlib.sha256((source/'worker.py').read_bytes()).hexdigest(),'candidate_worker_sha256':hashlib.sha256((D/'worker.py').read_bytes()).hexdigest(),'model_unchanged':(D/'model.py').read_bytes()==(source/'model.py').read_bytes(),'only_change':'Train-derived inverse window multiplicity factors applied to the existing state+gate loss. Preserve total train coefficient mass at each horizon; no changes to model, data, optimizer, LR, windows, normalization, original selection, or report equations. This is an untrained candidate, not an accuracy result.','tests':tests,'optimizer_updates':0,'cloud_launched':False,'evaluation_plan':{'comparison':'Original weighting vs corrected weighting, same gated checkpoint and optimizer/RNG state; train only, original validation selection plus separately reported startup/peak errors. Freeze candidate and criteria before any new comparison. Do not reuse old test outcomes for tuning.','acceptance':'Improve initial32s validation gas deficit and peak amplitude without worsening full-rollout four-state validation MAE or quiet drift materially; report all states and finite/negative/mass-increase checks. Thresholds and compute bounds must be frozen before launch. Previously inspected validation/test are development evidence, not pristine confirmation.','budget':'No launch until a carved reservation fits cumulative125USD and does not double-count the existing40USD Flex queue allowance. Existing queue is scheduled and has no VM as of last live read; never duplicate or cancel based only on stale metadata.'}}
 (R/'results/exposure-candidate-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
