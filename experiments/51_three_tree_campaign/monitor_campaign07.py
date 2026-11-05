"""Read-only rolling parent and actual resources, never resubmit."""
from cloud07 import *
import datetime
x=json.loads((P/('continuation-execution.json' if (P/'continuation-execution.json').exists() else 'execution.json')).read_text());s=gc('workflows','executions','describe',x['name'].split('/')[-1],'--workflow='+x['name'].split('/')[-3],'--location=us-central1')
jobs=gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id~t51r07');vms=gc('compute','instances','list','--filter=labels.trial_id~t51r07')
v=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),controller=s,jobs=jobs,vms=vms);save('status.json',v);print(json.dumps(v))
