"""Offline bounded-head checks, isolated gradients only; no optimizer."""
import copy,json,hashlib,sys
from pathlib import Path
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/gas-head-candidate';sys.path.insert(0,str(D));from gas_head import GasHead
torch.set_num_threads(4);plan=json.loads((D/'candidate-plan.json').read_text());proof=json.loads((R/'results/gas-head-candidate-prepared.json').read_text())
for name,info in proof['files'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==info['sha256']
a=np.load(D/'features.npz');x=torch.tensor(a['features']);base=torch.tensor(a['base_states']);truth=torch.tensor(a['truth']);ck=torch.load(D/'initial-head.pt',map_location='cpu',weights_only=False);head=GasHead(ck['feature_mean'],ck['feature_std']);head.load_state_dict(ck['model']);head.eval();before=copy.deepcopy(head.state_dict());train=np.array(plan['train_indices']);valid=np.array(plan['validation_indices']);meta=json.loads((R/'data/exposure-pilot02/schema.json').read_text());rot=meta['rotations'][0]
assert a['source_ids'][train].tolist()==rot['train'] and a['source_ids'][valid].tolist()==rot['validation'] and not set(a['source_ids'])&set(rot['test']);assert not set(a['configuration'][train])&set(a['configuration'][valid])
with torch.inference_mode():
 y=head(x,base[:,:,2]);assert torch.equal(y,base[:,:,2]);reconstructed=base.clone();reconstructed[:,:,2]=y;assert torch.equal(reconstructed,base)
 for bias,expected in [(-100,.5),(100,2)]:
  probe=copy.deepcopy(head);probe.net[-1].bias.fill_(bias);factor_probe=probe(x[:2],torch.ones_like(base[:2,:,2]));assert torch.allclose(factor_probe,torch.full_like(factor_probe,expected),rtol=1e-6,atol=1e-6)
 # Compare only the already-recorded baseline validation inference, not a new candidate score.
 actual=(base[valid]-truth[valid,1:]).abs().mean(1);config=a['configuration'][valid];mae=torch.stack([actual[torch.tensor(config==c)].mean(0) for c in np.unique(config)]).mean(0);old=json.loads((R/'results/exposure-pilot02-analysis.json').read_text())['arms'][0]['cpu_validation_replay']['rollout']['physical_MAE_by_feature'];assert np.allclose(mae.numpy(),old,rtol=.002,atol=0)
# Train-only isolated backward proves learnability of initialized head; no optimizer exists.
out=head(x[train[:32]],base[train[:32],:,2]);loss=(torch.asinh(out/.01)-torch.asinh(truth[train[:32],1:,2]/.01)).square().mean();loss.backward();gradients=[p.grad for p in head.parameters()];assert all(g is not None and torch.isfinite(g).all() for g in gradients);assert head.net[-1].weight.grad.norm()>0;assert all(torch.equal(v,before[k]) for k,v in head.state_dict().items())
result=dict(passed=True,optimizer_instantiated=False,optimizer_updates=0,initial_all_state_output_bitwise_equal=True,baseline_validation_replay_close=True,factor_bound_checks_passed=True,train_validation_configurations_disjoint=True,test_features_included=False,isolated_train_gradient_finite=True,initialized_last_layer_gradient_nonzero=True,head_state_unchanged=True,scope='Preparation/preflight only. No trained correction or accuracy improvement exists. Replays only already-recorded baseline validation metrics, not candidate selection. Other states and recurrent feedback remain frozen; gas/dry-fuel consistency requires an explicit future guard.')
(R/'results/gas-head-candidate-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
