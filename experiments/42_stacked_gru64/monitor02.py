"""Read-only cloud status; never submits jobs."""
from pathlib import Path
import sys,json,datetime
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc
p=json.loads((R/'results02/package.json').read_text());e=json.loads((R/'results02/execution.json').read_text())['name'];out={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution':gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1'),'candidates':{}}
for c in p['candidates']:
 v={'instances':gc('compute','instances','list','--filter=labels.trial_id='+c['label']),'disks':gc('compute','disks','list','--filter=labels.trial_id='+c['label'])}
 try:v['job']=gc('batch','jobs','describe',c['job_id'],'--location='+c['region'])
 except RuntimeError as err:v['lookup_error']=str(err)
 out['candidates'][c['id']]=v
(R/'results02/progress.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checked_utc':out['checked_utc'],'controller':out['execution']['state'],'candidates':{k:{'batch':v.get('job',{}).get('status',{}).get('state','absent/lookup error'),'vms':[{a:x.get(a) for a in ['name','status','zone']} for x in v['instances']]} for k,v in out['candidates'].items()}}))
