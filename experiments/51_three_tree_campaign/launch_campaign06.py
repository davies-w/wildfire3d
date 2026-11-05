"""Submit the approved gated rolling parent once, after preservation/readiness."""
from cloud06 import *
assert not (P/'submission-intent.json').exists(),'Never retry production submission'
assert json.loads((R/'private05/closed.json').read_text())['passed']
pkg=json.loads((P/'package.json').read_text());a=json.loads((P/'authorization.json').read_text())
for n,h in pkg['files'].items():assert sha(R/'data/cloud06'/n)==h
assert json.loads((P/'readiness-proof.json').read_text())['passed']
proof=json.loads((P/'preservation.json').read_text());assert proof['passed'] and proof['index_sha256']==pkg['index_sha256']
for kind in ['case','epoch','parent','check']:
 assert sha(R/('rolling06-'+kind+'.yaml'))==json.loads((P/('deployed-'+kind+'.json')).read_text())['sha256']
# Only explicitly successful dry runs may precede the production parent.
for e in gc('workflows','executions','list',WF,'--location=us-central1'):
 s=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF,'--location=us-central1');assert s['state']=='SUCCEEDED' and json.loads(s['argument'])['dry_run'] is True
assert not gc('compute','instances','list'),'Existing instances require reconciliation'
assert not gc('batch','jobs','list','--location=us-central1'),'Existing jobs require reconciliation'
assert not gc('compute','disks','list','--filter=labels.trial_id~t51r06')
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==a['cap_usd']
 hold=b['reservations'][RESERVATION];assert hold['state']=='reserved_before_upload' and hold['allowance_usd']==a['campaign_allowance_usd'];assert b['reservations']['fds-tree51-training']['allowance_usd']==20
 save('submission-intent.json',dict(time=time.time(),workflow=WF,index_sha256=pkg['index_sha256'],gate='onecase_then_independent_proof'))
 hold['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 e=gc('workflows','execute',WF,'--location=us-central1','--data={}');save('execution.json',e);hold.update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n');print('SUBMITTED ONCE',e['name'])
