"""Prepare continuation-specific cloud commands, never mutate campaign01."""
from pathlib import Path
R=Path(__file__).resolve().parent
s=(R/'cloud.py').read_text().replace("P=R/'private'","P=R/'private02'").replace('campaign01','campaign02');(R/'cloud02.py').write_text(s)
for source,target in [('deploy.py','deploy_campaign02.py'),('launch.py','launch_campaign02.py'),('monitor.py','monitor_campaign02.py'),('inspect_outputs.py','inspect_outputs02.py')]:
 s=(R/source).read_text().replace('from cloud import','from cloud02 import').replace('campaign01','campaign02')
 if source in ['deploy.py','launch.py']:
  s=s.replace("R/'workflow.yaml'","R/'workflow02.yaml'")
 if source=='deploy.py':
  s=s.replace('admission-v2.json','admission-v4.json')
  s=s.replace("R/'data/cloud'","R/'data/cloud02'").replace("R/'data/cloud/manifest.json'","R/'data/cloud02/manifest.json'")
  s=s.replace("[(WF,'workflow.yaml'),(WF+'-check','readiness.yaml')]","[(WF+'-wave','wave02.yaml'),(WF,'workflow02.yaml'),(WF+'-check','readiness02.yaml')]")
  s=s.replace("a=json.loads", "assert sha(R/'wave02.yaml')==pkg['wave_sha256']\na=json.loads")
  marker="if not (P/'readiness-execution.json').exists():"
  extra='''expiry=condition['expression'].split(" && ")[-1]
save('task-read-condition.json',dict(title='tree51-task-read02',expression=expiry))
gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/fdsTree51TaskReader','--condition-from-file='+str(P/'task-read-condition.json'))
# Only execution creation/read on this one child workflow, expiring with the campaign.
resource='projects/'+PROJECT+'/locations/us-central1/workflows/'+WF+'-wave'
save('wave-run-condition.json',dict(title='tree51-campaign02-wave-run',expression="resource.name.startsWith('"+resource+"') && "+expiry))
role='fdsTree51WaveRunner'
roles=gc('iam','roles','list','--filter=name:roles/'+role)
if not roles:gc('iam','roles','create',role,'--title=Tree51 child execution create and get','--permissions=workflows.executions.create,workflows.executions.get','--stage=GA')
actual=gc('iam','roles','describe',role);assert set(actual['includedPermissions'])=={'workflows.executions.create','workflows.executions.get'}
gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/'+role,'--condition-from-file='+str(P/'wave-run-condition.json'))
'''
  s=s.replace(marker,extra+marker)
 if source=='launch.py':
  s=s.replace("assert not (P/'submission-intent.json').exists()", "assert json.loads((R/'private/closed.json').read_text())['passed']\nassert sha(R/'wave02.yaml')==json.loads((P/'package.json').read_text())['wave_sha256']\nassert json.loads((P/'child-readiness-status.json').read_text())['state']=='SUCCEEDED'\nassert not (P/'submission-intent.json').exists()")
 if source=='monitor.py':
  s=s.replace("v=dict(supervisor=", "children=gc('workflows','executions','list',WF+'-wave','--location=us-central1')\nsave('child-executions.json',children)\nv=dict(children=children,supervisor=")
 (R/target).write_text(s)
