"""Read-only rolling parent and actual resources, never resubmit."""
from cloud05 import *
import datetime
x=json.loads((P/'execution.json').read_text());s=gc('workflows','executions','describe',x['name'].split('/')[-1],'--workflow='+WF,'--location=us-central1')
jobs=gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id~t51r05');vms=gc('compute','instances','list','--filter=labels.trial_id~t51r05')
v=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),controller=s,jobs=jobs,vms=vms);save('status.json',v);print(json.dumps(v))
