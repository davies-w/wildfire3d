"""Submit once after bounded admission, deployed readiness and preservation."""
from cloud04 import *
assert json.loads((R/'private03/closed.json').read_text())['passed']
assert sha(R/'wave04.yaml')==json.loads((P/'package.json').read_text())['wave_sha256']
assert json.loads((P/'child-readiness-status.json').read_text())['state']=='SUCCEEDED'
assert not (P/'submission-intent.json').exists(),'Submission already attempted; inspect instead'
a=json.loads((P/'authorization.json').read_text())
pkg=json.loads((P/'package.json').read_text());assert sha(R/'workflow04.yaml')==pkg['workflow_sha256']
e=json.loads((P/'readiness-execution.json').read_text());st=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1');save('readiness-status.json',st);assert st['state']=='SUCCEEDED'
assert not gc('compute','instances','list'),'Existing workers require reconciliation'
assert not gc('workflows','executions','list',WF,'--location=us-central1'),'Existing execution; no duplicate'
proof=json.loads((P/'preservation.json').read_text());assert proof['passed'] and proof['manifest_sha256']==pkg['manifest_sha256']
assert json.loads((P/'deployed-bootstrap-proof.json').read_text())['passed']
gc('artifacts','docker','images','describe',pkg['image_uri'])
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==a['cap_usd']
 assert b['reservations'][WF]['allowance_usd']==a['campaign_allowance_usd'] and b['reservations']['fds-tree51-training']['allowance_usd']==a['training_reserved_usd']
 save('submission-intent.json',dict(time=time.time(),workflow=WF,manifest_sha256=pkg['manifest_sha256']))
 b['reservations'][WF]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 e=gc('workflows','execute',WF,'--location=us-central1');save('execution.json',e);b['reservations'][WF].update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n');print('SUBMITTED',e['name'])
