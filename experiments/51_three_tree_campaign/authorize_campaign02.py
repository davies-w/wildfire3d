"""Use only the reconciled original allowance; no new reservation or spending cap."""
from cloud02 import *
assert not (P/'submission-intent.json').exists()
closed=json.loads((R/'private/closed.json').read_text());assert closed['passed'] and closed['remainder_reserved_to']==WF
b=json.loads(B.read_text());r=b['reservations'][WF];assert r['state']=='reserved_before_upload'
old=json.loads((R/'private/authorization.json').read_text());allowance=r['allowance_usd'];ancillary=old['ancillary_allowance_usd'];assert allowance>ancillary
assert b['reservations']['fds-tree51-training']['allowance_usd']==20 and b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200
save('authorization.json',dict(old,campaign_allowance_usd=allowance,compute_limit_usd=allowance-ancillary,scope='User explicitly requested corrected continuation of unfinished cases; original reconciled allowance only; training protected',recorded_unix=time.time()))
save('reservation.json',dict(passed=True,campaign_allowance_usd=allowance,compute_limit_usd=allowance-ancillary,training_reserved_usd=20,total_committed_usd=b['estimated_spend_usd']+b['reserved_usd'],authorized_usd=200))
print('Original remaining allowance reserved; training unchanged')
