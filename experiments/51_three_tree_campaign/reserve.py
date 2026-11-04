"""Reserve a bounded campaign and protect training inside the existing total cap."""
from cloud import *
assert not (P/'submission-intent.json').exists()
a=json.loads((P/'authorization.json').read_text())
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['authorized_usd']==a['cap_usd']
 keys={WF:a['campaign_allowance_usd'], 'fds-tree51-training':a['training_reserved_usd']}
 for key,amount in keys.items():
  if key in b['reservations']:assert b['reservations'][key]['allowance_usd']==amount
 additional=sum(v for k,v in keys.items() if k not in b['reservations'])
 assert b['estimated_spend_usd']+b['reserved_usd']+additional<=b['authorized_usd']
 for key,amount in keys.items():
  if key not in b['reservations']:b['reservations'][key]=dict(allowance_usd=amount,state='reserved_before_upload',reserved_unix=time.time(),scope='Budget-limited campaign; may stop short of2000' if key==WF else 'Protected future training funds; no training launched')
 b['reserved_usd']+=additional;B.write_text(json.dumps(b,indent=2)+'\n')
 save('reservation.json',dict(passed=True,campaign_allowance_usd=a['campaign_allowance_usd'],compute_limit_usd=a['compute_limit_usd'],ancillary_allowance_usd=a['ancillary_allowance_usd'],training_reserved_usd=a['training_reserved_usd'],total_committed_usd=b['estimated_spend_usd']+b['reserved_usd'],authorized_usd=b['authorized_usd']))
print('Reserved bounded campaign and training within cumulative cap')
