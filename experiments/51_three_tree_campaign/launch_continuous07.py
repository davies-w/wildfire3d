"""One-time continuation; never resubmit indices0..18 or the original parent."""
from cloud07 import *
assert not (P/'continuation-submission-intent.json').exists()
assert json.loads((P/'continuous-readiness.json').read_text())['passed']
for kind in ['case','epoch','parent']:
 assert json.loads((P/('continuous-deployed-'+kind+'.json')).read_text())['passed']
for args in [('batch','jobs','list','--location=us-central1'),('compute','instances','list'),('compute','disks','list')]:assert not gc(*args,'--filter=name~t51r07')
children=gc('workflows','executions','list',WF+'-case','--location=us-central1');assert all(x['state'] not in ['ACTIVE','QUEUED'] for x in children)
state=json.loads((P/'continuation-state.json').read_text())['state'];assert state['cursor']==19 and state['epoch']==2 and not state['active']
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200;assert b['reservations']['fds-tree51-training']['allowance_usd']==20
 h=b['reservations'][RESERVATION];assert h['state']=='submitted' and state['limit']<=int((h['allowance_usd']-10)*1000000)
 save('continuation-submission-intent.json',dict(time=time.time(),workflow=WF+'-resume1',cursor=19,excluded=[9,15]))
 e=gc('workflows','execute',WF+'-resume1','--location=us-central1','--data={}');save('continuation-execution.json',e);h.setdefault('continuations',[]).append(e['name']);B.write_text(json.dumps(b,indent=2)+'\n');print('SUBMITTED CONTINUATION ONCE',e['name'],flush=True)
(R/'continuation-record07.json').write_text(json.dumps(dict(workflow=WF+'-resume1',execution=e['name'].split('/')[-1],created_at=e['startTime'],first_index=19,remaining_never_submitted=1512,prior_successes_reported=17,prior_science_verified=17,excluded_pending_review=[9,15],local_admission_gate=False),indent=2)+'\n')
