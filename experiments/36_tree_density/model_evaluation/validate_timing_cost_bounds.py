"""Check conservative placement accounting and rejection of unbudgeted GPU combinations."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];source=R.parents[1]/'scripts/reconcile_runtime_costs.py'
spec=importlib.util.spec_from_file_location('runtime_costs',source);costs=importlib.util.module_from_spec(spec);spec.loader.exec_module(costs)
assert costs.runtime_rate('g2-standard-4','STANDARD','projects/p/zones/us-east4-a/instances/x')==1.2
assert costs.runtime_rate('g2-standard-4','STANDARD','projects/p/zones/us-central1-a/instances/x')==.706832276
try:costs.runtime_rate('g2-standard-4','STANDARD','projects/p/zones/europe-west4-a/instances/x')
except AssertionError:pass
else:raise AssertionError('Unverified regional price accepted')
good={'guestAccelerators':[{'acceleratorType':'zones/us-central1-f/acceleratorTypes/nvidia-tesla-t4','acceleratorCount':'1'}],'scheduling':{'provisioningModel':'STANDARD'}}
assert costs.budgeted_gpu_type('n1-standard-4',good)=='nvidia-tesla-t4'
for bad in [{},{'guestAccelerators':[{'acceleratorType':'nvidia-tesla-t4','acceleratorCount':2}]},{'guestAccelerators':[{'acceleratorType':'nvidia-tesla-v100','acceleratorCount':1}]}]:
 try:costs.budgeted_gpu_type('n1-standard-4',bad)
 except AssertionError:pass
 else:raise AssertionError('Unbudgeted GPU configuration accepted')
plan=json.loads((R/'results/timing-decoder-trial-plan05.json').read_text())['budget_plan'];price=json.loads((R/'results/timing-decoder-pilot05-price-bound.json').read_text());assert price['passed'] and price['extracted_max_usd_per_hour']<=1.2;assert plan['maximum_rate_bound_usd_per_hour']==1.2 and (plan['vm_creation_age_cap_s']+plan['shutdown_margin_s'])*1.2/3600<=plan['maximum_allowance_usd']==.45
proof=dict(passed=True,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),historical_central_rate_preserved=True,regional_rate_conservative=True,unknown_region_rejected=True,missing_multiple_and_different_gpu_rejected=True,regional_lifetime_compute_bound_usd=.45,price_proof_sha256=hashlib.sha256((R/'results/timing-decoder-pilot05-price-bound.json').read_bytes()).hexdigest(),optimizer_updates=0,scope='Cost-bound logic only. Shared charges remain project-level; not final billing or capacity evidence.')
(R/'results/timing-cost-bounds-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
