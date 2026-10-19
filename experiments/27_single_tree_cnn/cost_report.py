"""Conservative compute proxy from controller lifetimes; never an invoice claim."""
import json,time,datetime
from pathlib import Path
R=Path(__file__).parent;b=json.loads((R/'budget.json').read_text());rows=[]
def timestamp(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
for name,r in b['reservations'].items():
 p=R/'jobs'/name/'status.json'
 if not p.exists():continue
 s=json.loads(p.read_text());start=timestamp(s['startTime']);end=timestamp(s['endTime']) if s.get('endTime') else time.time();elapsed=max(0,end-start)
 rows.append(dict(group=name,workflow_state=s['state'],controller_lifetime_s=elapsed,compute_proxy_usd=elapsed/3600*b['rate_assumption_usd_per_vm_hour']))
a=dict(authorized_usd=b['authorized_usd'],reserved_usd=b['reserved_usd'],compute_proxy_usd=sum(r['compute_proxy_usd'] for r in rows),groups=rows,note='Assumes one VM per controller at ledger conservative0.08USD/hour for its entire observed controller lifetime, including provisioning/cleanup. Excludes storage, egress, logs/workflows. Not billed spend and not a current price quote. Reservations include ancillary/cleanup allowance; never recycled.')
(R/'results/cost-proxy.json').write_text(json.dumps(a,indent=2));print({k:v for k,v in a.items() if k!='groups'})
