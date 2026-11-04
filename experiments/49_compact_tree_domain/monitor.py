"""Read-only pilot status, persisted privately; never resubmits or releases resources."""
from cloud import *
import datetime
from zoneinfo import ZoneInfo
pkg=json.loads((P/'package.json').read_text());e=json.loads((P/'execution.json').read_text())
st=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF,'--location=us-central1')
vms=gc('compute','instances','list','--filter=labels.trial_id~tree49-compact01');jobs=gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id~tree49-compact01')
supervisor=None
if (P/'supervisor-execution.json').exists():
 se=json.loads((P/'supervisor-execution.json').read_text());supervisor=gc('workflows','executions','describe',se['name'].split('/')[-1],'--workflow='+WF+'-supervisor','--location=us-central1')
v=dict(supervisor=supervisor,checked_at=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),controller=st,jobs=jobs,vms=vms);save('status.json',v)
print(json.dumps(dict(checked_at=v['checked_at'],controller=st['state'],supervisor=supervisor['state'] if supervisor else None,jobs=[dict(name=j['name'],status=j.get('status')) for j in jobs],vms=[dict(name=x['name'],status=x['status'],zone=x['zone']) for x in vms]),indent=2))
