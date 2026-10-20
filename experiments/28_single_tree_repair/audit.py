"""Verify strict data separation, original freeze and budget conservation."""
import json,hashlib
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'27_single_tree_cnn'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for root in [P,R]:
 f=json.loads((root/'results/prediction-freeze.json').read_text());assert all(sha(root/p)==h for p,h in f['files'].items())
cases=json.loads((R/'cases.json').read_text());old=json.loads((P/'cases.json').read_text());tests=[c for c in cases if c['split']=='test'];assert len(tests)==6
assert not any(p.name.startswith('s27_test') for p in (R/'data/fields').glob('*'))
assert not any((c['wind_speed'],c['angle_deg'])==(o['wind_speed'],o['angle_deg']) for c in tests for o in old)
f=json.loads((R/'results/prediction-freeze.json').read_text());ledger=json.loads((P/'budget.json').read_text());res=[r for n,r in ledger['reservations'].items() if n.startswith('s28-')]
assert len(res)==6 and all(r['reserved_unix']>f['created_unix'] for r in res)
assert abs(sum(r['allowance_usd'] for r in ledger['reservations'].values())-ledger['reserved_usd'])<1e-6 and ledger['reserved_usd']<=5
report=dict(original_freeze_verified=True,revised_freeze_verified=True,fresh_conditions_distinct_from_all_original_conditions=True,old_tests_excluded_from_fitting=True,new_test_reservations_after_prediction_freeze=True,new_reservation_usd=sum(r['allowance_usd'] for r in res),central_reserved_usd=ledger['reserved_usd'],cap_usd=ledger['authorized_usd'])
(R/'results/audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
