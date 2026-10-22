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
 assert not (R/'budget.json').exists(),'Attempt already reserved; do not repeat'
 assert not gc('compute','instances','list')
 assert not gc('batch','jobs','list','--location=us-central1')
 deployed=gc('workflows','describe','fds-gpu29-test02','--location=us-central1')
 assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((R/'workflow.yaml').read_text())
 budget={'authorized_usd':1,'reserved_usd':.8,'attempt':'gpu29-test02','reserved_unix':time.time(),'state':'reserved','published_reference_usd_per_hour':.402748,'conservative_compute_rate_usd_per_hour':.8,'queue_limit_s':1800,'vm_age_limit_s':1200,'overall_deadline_s':3000,'compute_envelope_50min_usd':.8*3000/3600,'ancillary_cleanup_allowance_usd':.8-.8*3000/3600,'retries':0,'recycle_reservations':False}
 (R/'budget.json').write_text(json.dumps(budget,indent=2))
 result=gc('workflows','execute','fds-gpu29-test02','--location=us-central1');(R/'results/execution.json').write_text(json.dumps(result,indent=2));budget['state']='submitted';budget['execution']=result['name'];(R/'budget.json').write_text(json.dumps(budget,indent=2));print(result['name'])
