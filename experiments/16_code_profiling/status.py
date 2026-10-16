"""Save read-only final lifecycle evidence for the single approved trial."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';P='tmrw-wildfire-20261015'
def query(*args):
 p=subprocess.run([G,*args,'--project='+P,'--format=json'],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout)
def main():
 state=query('workflows','executions','describe','02052692-3206-4942-bfbc-db9e779733c4','--workflow=fds-profile16','--location=us-central1')
 (ROOT/'results/workflow-status.json').write_text(json.dumps(state,indent=2)+'\n')
 print('Workflow:',state['state'])
 if state['state']=='ACTIVE':return
 inventory={'instances':query('compute','instances','list'),'disks':query('compute','disks','list'),'jobs':query('batch','jobs','list','--location=us-central1')}
 (ROOT/'results/cleanup.json').write_text(json.dumps(inventory,indent=2)+'\n')
 subprocess.run([G,'storage','cp','gs://'+P+'-trial/profile16/job-status.json',str(ROOT/'results/job-status.json')],check=True)
 print('Remaining resources:',{k:len(v) for k,v in inventory.items()})
 if any(inventory.values()):raise RuntimeError('Cleanup is not complete; inspect resource inventory')
if __name__=='__main__':main()
