"""Private campaign affordability assessment. Never mutates the ledger or launches jobs."""
import gzip,json,statistics,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;E=R.parent
read=lambda p:json.loads(p.read_text())
b=read(E/'33_representation_loss/budget.json');rates=read(R/'private/c3-posted-rates.json')
assert len(rates)==2 and all(x['currency']=='USD' for x in rates)
rate=sum((4 if 'Core' in x['description'] else 32)*float(x['gross_cost'])/float(x['usage_quantity']) for x in rates)
compact=read(E/'49_compact_tree_domain/data/report/measurements.json')
oak=read(E/'50_live_oak/data/report/summary.json');closed=read(E/'50_live_oak/private/closed.json')
cases=[json.loads(x) for x in gzip.open(R/'data/cases.jsonl.gz','rt')]
reuse={c['reuse']['case'] for c in cases if c['reuse']}
small=[x['startup_to_completion_minutes'] for x in oak['cases'] if x['case'] in reuse]
assert len(small)==2
# Allocation overhead is a proxy from all10; only two allowed-size pilot measurements exist.
oak_minutes=statistics.mean(small)+closed['allocation_seconds']/600-oak['mean_minutes']
remaining={typ:sum(c['type_id']==typ and not c['reuse'] for c in cases) for typ in [1,2,3]}
hours=((remaining[1]+remaining[3])*compact['mean_vm_allocation_minutes']+remaining[2]*oak_minutes)/60
available=b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd']
result=dict(authorized_usd=b['authorized_usd'],estimated_spend_usd=b['estimated_spend_usd'],existing_reserved_usd=b['reserved_usd'],unreserved_usd=available,remaining_cases=remaining,vm_hours_scenario=hours,conservative_compute_usd=hours*.15,observed_unit_rate_usd_per_vm_hour=rate,observed_rate_compute_scenario_usd=hours*rate,illustrative_training_headroom_usd=20,admitted=False,reason='Conservative simulation compute plus training exceeds unreserved capacity; storage/transfer/recovery not yet bounded. Recent posted rate scenario is not a hard campaign bound.',assumptions=['No savings assumed for8-minute instead of5-minute checkpointing.','Two nominal-oak pilot samples do not characterize all four allowed geometries or all environments.','Training20USD is planning headroom, not a measured training guarantee.','No existing pending reserves released, no new allowance and no partial paid campaign launched.','Rates come from posted usage through Nov3 02UTC; not a guarantee of future Spot prices.'])
(R/'private/admission.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
