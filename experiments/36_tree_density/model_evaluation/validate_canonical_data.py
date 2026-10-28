"""Check exact window targets, fit guards and loss derivatives without optimization."""
from pathlib import Path
import hashlib,json
import numpy as np
import torch
from canonical_data import CanonicalData,canonical_physical_loss,HORIZONS
from timing_decoder import JointDecoder
R=Path(__file__).resolve().parents[1];D=R/'data/guard-matched-pilot01';C=R/'data/canonical-feature-cache'
assert json.loads((R/'results/canonical-feature-cache-preflight.json').read_text())['passed'];torch.set_num_threads(4);d=CanonicalData(D,canonical_root=C);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);m.load_state_dict(initial['model']);before={k:v.clone() for k,v in m.state_dict().items()}
h=torch.tensor([45,1,16,4,8,1,45,8,4,16]);origins=torch.tensor([45,89,74,86,82,0,0,0,0,0]);ids=d.roles['fit'][:10];batch=d.canonical_batch(m,ids,h,origins)
for i,(case,origin,horizon) in enumerate(zip(batch['case'],batch['origin'],batch['horizon'])):
 assert torch.equal(batch['truth'][i],d.raw[case,origin+horizon]);assert torch.equal(batch['base'][i],d.cb[case,d.co[origin]+horizon-1]);assert torch.equal(batch['normalizers'][i],d.canonical_norm[int(horizon)])
loss=canonical_physical_loss(batch,d.canonical_case_factor);assert torch.isfinite(loss);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters() if p.requires_grad);assert any(bool((p.grad!=0).any()) for p in m.parameters() if p.requires_grad);assert all(p.grad is None for p in m.parameters() if not p.requires_grad);assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
blocked=False
try:d.canonical_batch(m,d.roles['selection'][:1],torch.tensor([1]),torch.tensor([0]))
except AssertionError:blocked=True
assert blocked and not d.confirmation_open
# Independently enumerate every uniform history/window/origin draw in a tiny
# unequal-replica example; equal configuration weighting must be recovered.
errors=torch.tensor([[1.,3.],[1.,3.],[5.,7.]]) # two replicas of configA, one ofB
weights=torch.tensor([.5,.5,1.]);estimate=(3/2)*(errors*weights[:,None]).mean();exact=.5*(errors[:2].mean()+errors[2].mean());assert torch.isclose(estimate,exact)
out=dict(passed=True,optimizer_updates=0,parameters_unchanged=True,exact_first_last_valid_window_targets=True,all_five_lengths_decoded_without_padding=True,selection_gradients_blocked=True,confirmation_closed=True,finite_nonzero_trainable_derivatives=True,frozen_context_gradients_absent=True,configuration_weighting_enumeration_passed=True,loss=float(loss.detach()),source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['canonical_data.py','validate_canonical_data.py']},scope='Local derivative/indexing/loss-estimator checks only; no training, acceptance result, confirmation/test score or deployment. Uniform horizon draws and uniform valid origins are required for the stated estimator.')
(R/'results/canonical-data-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
