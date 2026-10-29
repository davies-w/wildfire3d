"""Read-only monitor; never submits or retries a job."""
from pathlib import Path
import sys,json,datetime
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc
execution=json.loads((R/'results02/execution.json').read_text())['name']
s=gc('workflows','executions','describe',execution.rsplit('/',1)[1],'--workflow=fds-gpu37-integral02','--location=us-central1')
result=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution=s,instances=gc('compute','instances','list','--filter=labels.trial_id=gpu37-integral02'))
try:result['job']=gc('batch','jobs','describe','fds-gpu37-integral02','--location=us-west4')
except RuntimeError as e:result['job_lookup_error']=str(e)
(R/'results02/progress.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(workflow_state=s['state'],job_state=result.get('job',{}).get('status',{}),instances=[dict(name=v['name'],status=v['status']) for v in result['instances']])))
