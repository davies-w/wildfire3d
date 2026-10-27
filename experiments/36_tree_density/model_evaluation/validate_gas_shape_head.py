"""Untrained full-forecast shape-head invariant checks; no optimizer/fitting."""
from pathlib import Path
import json
import numpy as np
import torch
from gas_shape_head import GasShapeHead
R=Path(__file__).resolve().parents[1];D=R/'data/gas-head-candidate';torch.set_num_threads(4);torch.manual_seed(3618);a=np.load(D/'features.npz');plan=json.loads((D/'candidate-plan.json').read_text());ids=plan['train_indices'];x=torch.tensor(a['features'][ids]);base=torch.tensor(a['base_states'][ids,:,2]);times=torch.tensor(a['time'][ids]);old=torch.load(D/'initial-head.pt',map_location='cpu',weights_only=False);model=GasShapeHead(old['feature_mean'],old['feature_std']);model.eval()
with torch.no_grad():assert torch.equal(model(x,base,times),base)
# Arbitrary synthetic parameter initialization is an invariant probe, not fitting.
probe=GasShapeHead(old['feature_mean'],old['feature_std']);torch.nn.init.normal_(probe.net[-1].weight,std=.5);torch.nn.init.normal_(probe.net[-1].bias,std=.5)
def integral(g,t):
 dt=t[:,1:]-t[:,:-1];w=.5*dt;w[:,:-1]+=.5*dt[:,1:];return (g*w).sum(1)
with torch.no_grad():
 y=probe(x,base,times);nonzero=base!=0;ratio=y[nonzero]/base[nonzero];assert ((ratio>=.5-1e-6)&(ratio<=2+1e-6)).all();assert torch.equal(torch.sign(y),torch.sign(base));errors={}
 for name,op in [('positive',lambda z:z.clamp_min(0)),('negative',lambda z:(-z).clamp_min(0))]:
  before=integral(op(base),times);after=integral(op(y),times);assert torch.allclose(before,after,rtol=2e-6,atol=1e-8);errors[name]=float((after-before).abs().max())
 synthetic=torch.tensor([[0.,0.,0.],[1.,2.,0.],[-1.,-2.,0.],[1.,-1.,2.]]);st=torch.tensor([[0.,1.,3.,4.]]).expand(4,-1);sx=torch.zeros(4,3,46);sy=probe(sx,synthetic,st);assert torch.isfinite(sy).all() and torch.allclose(integral(sy,st),integral(synthetic,st),rtol=2e-6,atol=1e-6)
loss=(model(x[:32],base[:32],times[:32])-torch.tensor(a['truth'][ids[:32],1:,2])).square().mean();loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters());assert model.net[-1].weight.grad.norm()>0
result=dict(passed=True,train_only=True,histories=len(ids),optimizer_instantiated=False,optimizer_updates=0,initial_output_bitwise_equal=True,arbitrary_probe_factor_bounds_and_signs_preserved=True,positive_negative_integrals_preserved=True,max_integral_float32_residual_kg=errors,synthetic_zero_positive_negative_mixed_cases_passed=True,isolated_gradient_finite_and_nonzero=True,scope='Untrained architecture invariant checks only. Normalization uses each complete generated base forecast and known times, never future truth. This is a full-forecast output transform, not a causal one-step recurrent correction. It deliberately preserves the baseline total-release error and does not repair dry fuel/water/heating. No validation/test outcomes used, fit, improved accuracy or launch.')
(R/'results/gas-shape-head-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
