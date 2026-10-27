"""Posthoc completed-development trajectory; never reselect the failed primary."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1];D=R/'data/gas-head-pilot01';OUT=R/'data/gas-head-pilot01-results';sys.path.insert(0,str(D));from gas_head_metrics import acceptance
assert json.loads((R/'results/gas-head-pilot01-collected.json').read_text())['experiment_complete'];p=json.loads((D/'pilot-plan.json').read_text());n=json.loads((D/'base-normalization.json').read_text());baseline=json.loads((OUT/'baseline.json').read_text());arms={}
for arm in ['encoded_only','peak_aware']:
 rows=[]
 for ep in range(10,301,10):
  row=json.loads((OUT/f'{arm}-epoch{ep:03}.json').read_text());r=row['validation'];checks=acceptance(baseline,r,p['acceptance_all_required'],n['physical_encoding_scales']);rows.append(dict(epoch=ep,checks=checks,all_acceptance_pass=all(checks.values()),validation=r,train=row['train']))
 best=min(rows,key=lambda row:row['validation']['startup_gas_p90_deficit']);arms[arm]=dict(selected_epoch=json.loads((OUT/f'{arm}-selection.json').read_text())['epoch'],any_epoch_passes_all_frozen_acceptance=any(r['all_acceptance_pass'] for r in rows),best_startup_epoch_posthoc=best['epoch'],best_startup_relative_reduction=1-best['validation']['startup_gas_p90_deficit']/baseline['startup_gas_p90_deficit'],best_startup_failed_checks=[k for k,v in best['checks'].items() if not v],rows=rows)
out=dict(baseline=baseline,arms=arms,primary_trial_remains_failed=True,scope='Posthoc audit of all completed candidate-validation checkpoints. No reselection, altered acceptance, new fitting or test evaluation. An exploratory checkpoint can motivate a new prospective experiment but cannot rescue the predeclared failed trial. No sampled checkpoint passes every frozen acceptance check.')
assert not any(v['any_epoch_passes_all_frozen_acceptance'] for v in arms.values());(R/'results/gas-head-trajectory-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='rows'} for k,v in arms.items()},indent=2));r=next(row for row in arms['peak_aware']['rows'] if row['epoch']==180);print(json.dumps({k:r['validation'][k] for k in ['startup_gas_p90_deficit','peak_release_MAE_kg_s','released_fuel_integral_MAE_kg','objective','gas_dry_fuel_consistency_residual_kg']},indent=2))
