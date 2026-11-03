"""Submit exactly one authorized cloud controller after readiness and preservation."""
from cloud48_05 import *
assert not (P/'submission-intent.json').exists(),'Submission already attempted: inspect, do not repeat'
pkg=json.loads((P/'package.json').read_text());assert sha(R/'pilot05.yaml')==pkg['workflow_sha256']
e=json.loads((P/'readiness-execution.json').read_text());st=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1');save('readiness-status.json',st);assert st['state']=='SUCCEEDED'
assert not gc('compute','instances','list'),'Existing workers require reconciliation'
assert not gc('workflows','executions','list',WF,'--location=us-central1'),'Existing execution; do not duplicate'
q={x['metric']:x['limit']-x['usage'] for x in gc('compute','regions','describe','us-central1')['quotas']};assert q['PREEMPTIBLE_CPUS']>=80 and q['IN_USE_ADDRESSES']>=20 and q['SSD_TOTAL_GB']>=600
assert json.loads((P/'preservation.json').read_text())['passed']
gc('artifacts','docker','images','describe',pkg['image_uri'])
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd'];assert b['reservations'][WF]['allowance_usd']>=17
 save('submission-intent.json',dict(time=time.time(),workflow=WF,input_sha256=pkg['input_sha256']))
 b['reservations'][WF]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 e=gc('workflows','execute',WF,'--location=us-central1');save('execution.json',e);b['reservations'][WF].update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n');print('SUBMITTED',e['name'])
