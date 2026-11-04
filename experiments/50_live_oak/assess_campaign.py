"""Private planning scenario; does not reserve funds or launch work."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def read(p):
    return json.loads(p.read_text())

def main():
    ledger = read(ROOT / 'experiments/33_representation_loss/budget.json')
    compact = read(ROOT / 'experiments/49_compact_tree_domain/private/closed.json')
    oak = read(HERE / 'private/closed.json')
    # Use audited allocation time, including provisioning, for both pilots.
    compact_mean = compact['allocation_seconds'] / 22 / 3600
    oak_mean = oak['allocation_seconds'] / 10 / 3600
    remaining_compute = (1980 * compact_mean + 990 * oak_mean) * .15
    available = ledger['authorized_usd'] - ledger['estimated_spend_usd'] - ledger['reserved_usd']
    result = dict(cap_usd=ledger['authorized_usd'], estimated_spend_usd=ledger['estimated_spend_usd'],
        pending_reserved_usd=ledger['reserved_usd'], unreserved_usd=available,
        remaining_cases=2970, reusable_baseline_pilot_cases=30,
        conservative_vm_rate_usd_per_hour=.15,
        compact_mean_allocation_minutes=compact_mean*60, oak_mean_allocation_minutes=oak_mean*60,
        remaining_compute_scenario_usd=remaining_compute,
        illustrative_training_headroom_usd=20,
        shortfall_before_new_storage_transfer_usd=remaining_compute+20-available,
        fits_current_unreserved_budget=remaining_compute+20<=available,
        limitations=[
            'Scenario, not a statistical forecast or posted bill: pilots are stratified, not random samples.',
            'Pine/eucalyptus proxy uses all22 compact allocations, including two height controls; no precise per-type forecast.',
            'No extra allowance, reservation release, or new paid jobs authorized by this calculation.',
            'Training20USD is illustrative headroom, not a measured training estimate; new storage, transfer and retries are extra.',
            'Reconcile pending actual charges and establish a lower verified compute cost or revised scope before bulk launch; preserve physics and180s target.'])
    (HERE/'private/campaign-budget-assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
