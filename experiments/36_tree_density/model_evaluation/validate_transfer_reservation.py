"""Synthetic overlap fixtures; no cloud or ledger mutation."""
from pathlib import Path
import datetime,hashlib,json
from reconcile_transfer_reservation import posted_overlap,BUCKET,SKU
start=datetime.datetime(2026,10,26,20,38,tzinfo=datetime.timezone.utc)
def row(**kw):return dict(service='Cloud Storage',sku=SKU,resource_name=BUCKET,currency='USD',cost_type='regular',net_cost='16.0',first_usage_start='2026-10-27 04:00:00',last_usage_end='2026-10-27 17:00:00',**kw)
r=row();mixed={**r,'first_usage_start':'2026-10-26 04:00:00','net_cost':'.6'};other={**r,'resource_name':'unrelated-bucket'};ops={**r,'sku':'Regional Standard Class A Operations'}
a,b=posted_overlap([r,mixed,other,ops],start);assert a==16 and b==[r]
assert posted_overlap([r,mixed,other,ops],start)==posted_overlap([r,mixed,other,ops],start)
try:posted_overlap([{**r,'currency':'GBP'}],start)
except AssertionError:pass
else:raise AssertionError('Currency mismatch accepted')
R=Path(__file__).resolve().parents[1];proof=dict(passed=True,mixed_period_other_bucket_and_operations_excluded=True,stable_full_snapshot_sum=True,currency_mismatch_rejected=True,ledger_mutations=0,source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['reconcile_transfer_reservation.py','validate_transfer_reservation.py']});(R/'results/transfer-reservation-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
