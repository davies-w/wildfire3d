"""Compare cached canonical scores to independent real-prefix evaluation and exercise guards."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
import torch
from canonical_data import CanonicalData
from canonical_metrics import CANONICAL_LIMIT,canonical_checks,checks,select
from joint_metrics import checks as old_checks
from joint_predictor import FrozenJointPredictor
from joint_scorecard import horizon_scorecard
from timing_decoder import JointDecoder
R=Path(__file__).resolve().parents[1];D=R/'data/guard-matched-pilot01';S=R/'data/exposure-pilot02';torch.set_num_threads(4);d=CanonicalData(D,canonical_root=R/'data/canonical-feature-cache');ids=d.roles['fit'][:16];initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);selected=torch.load(R/'data/guard-matched-pilot01-results/balanced_tail-selected.pt',map_location='cpu',weights_only=False);decoder=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);decoder.load_state_dict(selected['model']);before={k:v.clone() for k,v in decoder.state_dict().items()};cached=d.score_canonical(decoder,ids)
sys.path.insert(0,str(S));from model import Transition
ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);schema=json.loads((S/'schema.json').read_text());source=np.load(S/'data/sequences.npz');source_ids=d.source_ids[ids.numpy()];geometry=torch.tensor(source['geometry'][source_ids]);predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],d.scales,torch.tensor(schema['external_scales']),decoder);reference,_=horizon_scorecard(predictor,d.raw[ids],geometry,d.times[ids],d.config[ids],d.labels[ids]);agreement={}
for h in ['1','4','8','16','45']:
 assert cached[h]['steps']==reference[h]['steps'] and cached[h]['finite'] and reference[h]['finite'];assert cached[h]['actual_duration_min_s']==reference[h]['actual_duration_min_s'] and cached[h]['actual_duration_max_s']==reference[h]['actual_duration_max_s']
 assert np.allclose(cached[h]['model_MAE'],reference[h]['model_MAE'],rtol=.001,atol=1e-7);assert np.allclose(cached[h]['no_change_MAE'],reference[h]['no_change_MAE'],rtol=1e-6,atol=1e-7)
 for phase in ['active','quiet','weak','transition']:
  a,b=cached[h]['phases'][phase],reference[h]['phases'][phase]
  for key in ['points','eligible_histories','eligible_configurations']:assert a[key]==b[key]
  if a['model_MAE'] is None:assert b['model_MAE'] is None
  else:assert np.allclose(a['model_MAE'],b['model_MAE'],rtol=.001,atol=1e-7)
 agreement[h]=dict(cached_MAE=cached[h]['model_MAE'],independent_MAE=reference[h]['model_MAE'])
# Real baseline numbers with deliberately synthetic improvement/violation rows.
base=json.loads((R/'data/guard-matched-pilot01-results/selection-baseline.json').read_text());base['canonical']=d.score_canonical(None,ids);candidate=copy.deepcopy(base)
for regime in ['autonomous','display']:
 for field in ['physical_MAE_by_feature']:candidate[regime][field]=[v*.8 for v in base[regime][field]]
 for field in ['startup_gas_p90_deficit','peak_release_MAE_kg_s']:candidate[regime][field]*=.8
for row in candidate['canonical'].values():row['model_MAE']=[v*.8 for v in row['model_MAE']]
plan=json.loads((D/'trial-plan.json').read_text());k=plan['acceptance'];scales=d.scales.tolist();legacy=old_checks(base,candidate,k,scales);extended=checks(base,candidate,k,scales);assert all(legacy.values()) and all(extended.values());assert all(extended[key]==v for key,v in legacy.items())
rows=[dict(epoch=-1,metrics=base),dict(epoch=10,metrics=candidate)];chosen,accepted=select(base,rows,k,scales);assert accepted and chosen['epoch']==10
blocked=[]
for h in ['1','4','8','16','45']:
 for state in range(4):
  bad=copy.deepcopy(candidate);bad['canonical'][h]['model_MAE'][state]=base['canonical'][h]['model_MAE'][state]*1.051;chosen,accepted=select(base,[rows[0],dict(epoch=10,metrics=bad)],k,scales);assert not accepted and chosen['epoch']==-1;blocked.append([h,state])
assert len(blocked)==20 and CANONICAL_LIMIT==.05 and not d.confirmation_open;assert all(torch.equal(v,before[key]) for key,v in decoder.state_dict().items());assert all(torch.equal(v,ck['model'][key]) for key,v in model.state_dict().items())
out=dict(passed=True,fit_histories=16,optimizer_updates=0,all_origins_all_five_horizons_match_independent_prefix_interface=True,all_phase_counts_and_MAE_match=True,original_acceptance_checks_preserved_exactly=True,all20_single_state_horizon_regressions_rejected=True,raw_fallback_preserved=True,parameters_unchanged=True,confirmation_and_test_not_evaluated=True,agreement=agreement,source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['canonical_data.py','canonical_metrics.py','validate_canonical_metrics.py']},scope='Scorer and selection-fixture validation only, not new fitted performance or independent generalization. Explicit prospective canonical guard5percent overall state MAE at every horizon; phase tables retained separately. Original10percent gallery/startup and all other gates unchanged.')
(R/'results/canonical-metrics-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='agreement'},indent=2))
