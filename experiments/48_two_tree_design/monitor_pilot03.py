"""Read-only pilot status, persisted privately; never resubmits or releases resources."""
from cloud48_03 import *
import datetime
from zoneinfo import ZoneInfo
pkg=json.loads((P/'package.json').read_text());e=json.loads((P/'execution.json').read_text())
st=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF,'--location=us-central1')
vms=gc('compute','instances','list','--filter=labels.trial_id~tree48-pilot03');jobs=gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id~tree48-pilot03')
v=dict(checked_at=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),controller=st,jobs=jobs,vms=vms);save('status.json',v)
print(json.dumps(dict(checked_at=v['checked_at'],controller=st['state'],jobs=[dict(name=j['name'],status=j.get('status')) for j in jobs],vms=[dict(name=x['name'],status=x['status'],zone=x['zone']) for x in vms]),indent=2))
