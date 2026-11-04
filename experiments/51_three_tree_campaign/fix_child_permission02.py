"""Approval-required IAM correction. Do not execute without explicit project-scope approval."""
from cloud02 import *
import sys
assert '--approved-project-execution-scope' in sys.argv,'Explicit user approval required after auto-review rejection'
assert not (P/'submission-intent.json').exists()
file=P/'wave-run-condition.json';old=json.loads(file.read_text());assert old['title']=='tree51-campaign02-wave-run'
if 'resource.name' in old['expression']:
 save('wave-run-condition-unsupported.json',old)
 gc('projects','remove-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/fdsTree51WaveRunner','--condition-from-file='+str(file))
 old['expression']=old['expression'].split(' && ')[-1];save(file.name,old)
role=gc('iam','roles','describe','fdsTree51WaveRunner');assert set(role['includedPermissions'])=={'workflows.executions.create','workflows.executions.get'}
gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/fdsTree51WaveRunner','--condition-from-file='+str(file))
print('Only execution create/get, expiring; no IAM/deploy/compute permissions added')
