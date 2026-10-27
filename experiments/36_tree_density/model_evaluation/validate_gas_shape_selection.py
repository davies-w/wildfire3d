"""Prospective selection checks with synthetic metric perturbations; no fitting."""
from pathlib import Path
import copy,json
from gas_shape_metrics import eligible,acceptance,selection_key
R=Path(__file__).resolve().parents[1];p=json.loads((R/'results/gas-shape-pilot-plan.json').read_text());b=json.loads((R/'results/gas-head-metrics-preflight.json').read_text())['baseline_replay'];k=p['acceptance_all_required'];scales=[1,1,.01,100];assert eligible(b,b,k,scales)
c=copy.deepcopy(b);c['startup_gas_p90_deficit']*=.8;c['peak_release_MAE_kg_s']*=.9;c['objective']*=1.04;assert eligible(b,c,k,scales) and all(acceptance(b,c,k,scales).values());assert selection_key(dict(epoch=10,validation=c))<selection_key(dict(epoch=0,validation=b))
for key in ['objective','released_fuel_integral_MAE_kg','gas_dry_fuel_consistency_residual_kg','peak_time_MAE_s','startup_gas_p90_overprediction']:
 bad=copy.deepcopy(c);bad[key]=b[key]*1.06;assert not eligible(b,bad,k,scales),key
bad=copy.deepcopy(c);bad['peak_release_MAE_kg_s']=b['peak_release_MAE_kg_s']*1.001;assert not eligible(b,bad,k,scales)
bad=copy.deepcopy(c);bad['physical_MAE_by_feature'][2]=b['physical_MAE_by_feature'][2]*1.06;assert not eligible(b,bad,k,scales)
bad=copy.deepcopy(c);bad['quiet_physical_MAE'][2]=b['quiet_physical_MAE'][2]+.002*.01;assert not eligible(b,bad,k,scales)
assert selection_key(dict(epoch=10,validation=c))<selection_key(dict(epoch=20,validation=c))
checks=acceptance(b,b,k,scales);assert not checks['startup_gas'] and not checks['peak_amplitude']
out=dict(passed=True,synthetic_metric_cases_only=True,optimizer_updates=0,baseline_eligible_but_cannot_pass_improvement=True,original_objective_tradeoff_within5pct_allowed=True,all_safeguard_violations_rejected=True,overprediction_guard_enforced=True,ties_prefer_earlier_epoch=True,scope='Selection-code checks only, no newly fitted shape-head validation metrics, model selection or launch. Prior trial remains failed.')
(R/'results/gas-shape-selection-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
