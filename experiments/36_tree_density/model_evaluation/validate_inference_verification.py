"""Verify the final paired evaluator on fit data only; no accepted-model or test claim."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
from inference_verification import evaluate_prefix_pair
from canonical_data import CanonicalData
from joint_predictor import FrozenJointPredictor
from timing_decoder import JointDecoder
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';D=R/'data/guard-matched-pilot01';torch.set_num_threads(4);d=CanonicalData(D,canonical_root=R/'data/canonical-feature-cache');ids=d.roles['fit'][:8];initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);selected=torch.load(R/'data/guard-matched-pilot01-results/balanced_tail-selected.pt',map_location='cpu',weights_only=False);decoder=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);decoder.load_state_dict(selected['model']);before={k:v.clone() for k,v in decoder.state_dict().items()};ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);sys.path.insert(0,str(S));from model import Transition
model=Transition('gated');model.load_state_dict(ck['model']);schema=json.loads((S/'schema.json').read_text());source=np.load(S/'data/sequences.npz');source_ids=d.source_ids[ids.numpy()];geometry=torch.tensor(source['geometry'][source_ids]);predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],d.scales,torch.tensor(schema['external_scales']),decoder)
actual,arrays=evaluate_prefix_pair(predictor,d.raw[ids],geometry,d.times[ids],d.config[ids],d.labels[ids],d.scales,d.std);reference={'candidate':d.score(decoder,ids),'baseline':d.score(None,ids),'no_change':d.score(None,ids,no_change=True)}
for name in reference:
 for regime in ['autonomous','display']:
  a,b=actual[name][regime],reference[name][regime];assert np.allclose(a['physical_MAE_by_feature'],b['physical_MAE_by_feature'],rtol=.001,atol=1e-7);assert np.isclose(a['objective'],b['objective'],rtol=.001,atol=1e-8);assert abs(a['startup_gas_p90_deficit']-b['startup_gas_p90_deficit'])<.002
 for h in ['1','4','8','16','45']:
  a,b=actual[name]['canonical'][h],reference[name]['canonical'][h];assert np.allclose(a['model_MAE'],b['model_MAE'],rtol=.001,atol=1e-7)
  for phase in ['active','quiet','weak','transition']:
   u,v=a['phases'][phase],b['phases'][phase];assert all(u[k]==v[k] for k in ['points','eligible_histories','eligible_configurations'])
assert all(actual['constraints'][k] for k in ['finite','mass_nonnegative','gas_nonnegative','coherent_mass_nonincreasing']);assert all(torch.equal(v,before[k]) for k,v in decoder.state_dict().items());assert all(torch.equal(v,ck['model'][k]) for k,v in model.state_dict().items());assert not d.confirmation_open
out=dict(passed=True,fit_histories=8,optimizer_updates=0,all382_coherent_forecasts_per_history_evaluated=True,actual_prefix_gallery_and_canonical_scores_match_cached_reference=True,raw_and_no_change_comparators_verified=True,coherent_forecast_constraints=actual['constraints'],parameters_unchanged=True,confirmation_and_test_not_evaluated=True,source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['inference_verification.py','validate_inference_verification.py']},scope='Final evaluator validation using an unaccepted prior checkpoint on fit histories only. This does not accept that model, inspect test outcomes, or prove a repair.')
(R/'results/inference-verification-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
