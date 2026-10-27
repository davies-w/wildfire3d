"""Posthoc validation trajectory audit; never reselect or alter acceptance."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'data/exposure-pilot02-results'
proof=json.loads((R/'results/exposure-pilot02-collected.json').read_text())
assert proof['passed'] and proof['experiment_complete'] and proof['cleanup_verified']
arms={}
for arm in ['original','corrected']:
 rows=[json.loads((p/(f'{arm}-epoch{i:03}.json' if i else f'{arm}-baseline.json')).read_text()) for i in range(13)]
 b=rows[0];d0=b['diagnostics']['startup_gas_p90_deficit'];p0=b['validation']['rollout']['peak_release_MAE_kg_s']
 best=min(rows,key=lambda r:r['diagnostics']['startup_gas_p90_deficit'])
 arms[arm]=dict(selected_epoch=json.loads((p/f'{arm}-selection.json').read_text())['epoch'],best_startup_epoch_posthoc=best['epoch'],best_startup_p90=best['diagnostics']['startup_gas_p90_deficit'],best_startup_relative_reduction=1-best['diagnostics']['startup_gas_p90_deficit']/d0,any_epoch_meets_startup_10pct=any(r['diagnostics']['startup_gas_p90_deficit']<=.9*d0 for r in rows),rows=[dict(epoch=r['epoch'],objective=r['validation']['rollout']['objective'],startup_p90=r['diagnostics']['startup_gas_p90_deficit'],peak_MAE_kg_s=r['validation']['rollout']['peak_release_MAE_kg_s'],startup_relative_reduction=1-r['diagnostics']['startup_gas_p90_deficit']/d0,peak_relative_reduction=1-r['validation']['rollout']['peak_release_MAE_kg_s']/p0) for r in rows])
out=dict(scope='Posthoc diagnosis of every completed development-validation epoch; no reselection, acceptance changes, test evaluation or optimizer updates. Best observed epochs are exploratory and cannot be treated as independent confirmation.',arms=arms,selection_alone_cannot_explain_failure=not any(x['any_epoch_meets_startup_10pct'] for x in arms.values()),interpretation='No sampled continuation epoch achieved the frozen startup improvement, even before other constraints. This does not rule out multiplicity correction from scratch, longer training or another learning rate.')
(R/'results/exposure-pilot02-trajectory-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='rows'} for k,v in arms.items()},indent=2))
