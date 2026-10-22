"""Explicit deployment/admission/status. No paid launch from DVC."""
import argparse
import fcntl
import json
import subprocess
import time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud'
PROJECT='tmrw-wildfire-20261015'; WORKFLOW='fds-composition19'
def gc(*args):
    p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],capture_output=True,text=True,timeout=120)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout or '{}')
def deploy():
    previous=gc('workflows','describe','fds-domain17','--location=us-central1')
    response=gc('workflows','deploy',WORKFLOW,'--location=us-central1','--source='+str(ROOT/'workflow.yaml'),
                '--service-account='+previous['serviceAccount'])
    print('Deployed',response.get('name',WORKFLOW),'without executing.')
def launch():
    with (ROOT/'data/launch.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        marker=ROOT/'results/job-reservation.json'
        if marker.exists():raise RuntimeError('Single-job allowance already reserved')
        assert all(r['completed'] for r in json.loads((ROOT/'results/local-preflight.json').read_text()))
        assert json.loads((ROOT/'results/design-check.json').read_text())['passed']
        assert json.loads((ROOT/'results/model-smoke.json').read_text())['passed']
        assert json.loads((ROOT/'results/pipeline-check.json').read_text())['passed']
        assert all(r['passed'] for r in json.loads((ROOT/'results/acquisition-check.json').read_text()))
        j=json.loads((ROOT/'job.json').read_text());s=j['taskGroups'][0]['taskSpec']
        p=j['allocationPolicy']['instances'][0]['policy']
        assert s['maxRetryCount']==0 and s['maxRunDuration']=='17640s'
        assert j['taskGroups'][0]['taskCount']=='1' and p['machineType']=='c3-standard-4' and p['provisioningModel']=='SPOT'
        for w in gc('workflows','list','--location=us-central1'):
            if gc('workflows','executions','list',w['name'].split('/')[-1],'--location=us-central1','--filter=state=ACTIVE'):
                raise RuntimeError('Active controller exists')
        if gc('batch','jobs','list','--location=us-central1') or gc('compute','instances','list'):
            raise RuntimeError('Existing job/VM')
        deployed=gc('workflows','describe',WORKFLOW,'--location=us-central1')
        assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((ROOT/'workflow.yaml').read_text())
        r=dict(allowance_usd=.45,state='reserved',created_unix=time.time())
        marker.write_text(json.dumps(r,indent=2)+'\n')
        result=gc('workflows','execute',WORKFLOW,'--location=us-central1')
        r.update(state='submitted',execution=result['name'])
        marker.write_text(json.dumps(r,indent=2)+'\n')
        print(json.dumps(result,indent=2))
def status():
    name=json.loads((ROOT/'results/job-reservation.json').read_text())['execution'].split('/')[-1]
    s=gc('workflows','executions','describe',name,'--workflow='+WORKFLOW,'--location=us-central1')
    (ROOT/'results/workflow-status.json').write_text(json.dumps(s,indent=2)+'\n')
    print('Workflow:',s['state'])
    if s['state']=='ACTIVE':return
    inventory={k:gc(*a) for k,a in {'instances':('compute','instances','list'),
        'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
    (ROOT/'results/cleanup.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print({k:len(v) for k,v in inventory.items()})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['deploy','launch','status'])
    globals()[parser.parse_args().action]()
