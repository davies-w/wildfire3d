"""Replay existing baseline metrics before any new training or selection."""
from pathlib import Path
import json
import numpy as np
import torch
from gas_head_metrics import evaluate,acceptance
R=Path(__file__).resolve().parents[1];D=R/'data/gas-head-candidate';a=np.load(D/'features.npz');p=json.loads((D/'candidate-plan.json').read_text());n=json.loads((D/'base-normalization.json').read_text());ids=p['validation_indices'];torch.set_num_threads(4)
t=lambda key:torch.tensor(a[key][ids]);base=t('base_states');r=evaluate(base[:,:,2],base,t('truth'),t('time'),t('configuration'),t('activity_labels'),torch.tensor(n['physical_encoding_scales']),torch.tensor(n['std']));old=json.loads((R/'results/exposure-pilot02-analysis.json').read_text())['arms'][0];b=old['gpu_row']['validation']['rollout'];d=old['gpu_row']['diagnostics']
keys=['objective','physical_MAE_by_feature','peak_release_MAE_kg_s','peak_time_MAE_s','released_fuel_integral_MAE_kg','negative_fraction_by_feature','negative_magnitude_mean_by_feature','mass_increase_fraction','mass_increase_total_kg']
for k in keys:assert np.allclose(r[k],b[k],rtol=.002,atol=1e-7),(k,r[k],b[k])
for k in ['startup_gas_p90_deficit','quiet_physical_MAE']:assert np.allclose(r[k],d[k],rtol=.002,atol=1e-7),(k,r[k],d[k])
plan=json.loads((R/'results/gas-head-pilot-plan.json').read_text());checks=acceptance(r,r,plan['acceptance_all_required'],n['physical_encoding_scales']);assert not checks['startup_gas'] and not checks['peak_amplitude'] and all(v for k,v in checks.items() if k not in ['startup_gas','peak_amplitude'])
proof=dict(passed=True,baseline_replay=r,checked_existing_metrics=keys+['startup_gas_p90_deficit','quiet_physical_MAE'],identity_cannot_pass_improvement_gates=True,test_evaluated=False,optimizer_updates=0,scope='Already examined validation baseline only. New gas/dry-fuel consistency guard is a derived-measure check, not physical validation. No fitted-head score or selection.')
(R/'results/gas-head-metrics-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
