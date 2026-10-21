import json,subprocess,time,fcntl
from pathlib import Path
import yaml
R=Path(__file__).parent;G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';P='tmrw-wildfire-20261015'
def gc(*a):
 p=subprocess.run([G,*a,'--project='+P,'--format=json'],text=True,capture_output=True,timeout=120)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
with (R/'data/launch.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert json.loads((R/'budget.json').read_text())['state']=='prepared','Attempt already submitted; do not repeat'
 assert not gc('compute','instances','list')
 assert not gc('batch','jobs','list','--location=us-central1')
 deployed=gc('workflows','describe','fds-gpu30-sequence01','--location=us-central1')
 assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((R/'workflow.yaml').read_text())
 budget=json.loads((R/'budget.json').read_text());budget['state']='reserved'
 (R/'budget.json').write_text(json.dumps(budget,indent=2))
 result=gc('workflows','execute','fds-gpu30-sequence01','--location=us-central1');(R/'results/execution.json').write_text(json.dumps(result,indent=2));budget['state']='submitted';budget['execution']=result['name'];(R/'budget.json').write_text(json.dumps(budget,indent=2));print(result['name'])
