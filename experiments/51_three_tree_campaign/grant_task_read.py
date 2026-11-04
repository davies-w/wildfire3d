"""Temporary least-privilege task-status read access for the adaptive controller."""
from cloud import *
import datetime
assert not (P/'submission-intent.json').exists()
role='fdsTree51TaskReader'
p=subprocess.run([G,'iam','roles','describe',role,'--project='+PROJECT,'--format=json'],capture_output=True,text=True)
if p.returncode:
 assert 'NOT_FOUND' in p.stderr or 'does not exist' in p.stderr,p.stderr
 gc('iam','roles','create',role,'--title=Tree51 task status reader','--permissions=batch.tasks.list','--stage=GA')
else:assert json.loads(p.stdout)['includedPermissions']==['batch.tasks.list']
condition=dict(title='tree51-task-read',expression="request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=96)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')")
if not (P/'task-read-condition.json').exists():save('task-read-condition.json',condition)
gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/'+role,'--condition-from-file='+str(P/'task-read-condition.json'))
print('Granted only batch.tasks.list to the controller, with an expiring campaign condition')
