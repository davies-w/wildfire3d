import json,subprocess,fcntl,time
from pathlib import Path
R=Path(__file__).parent;G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';P='tmrw-wildfire-20261015'
def gc(*a):
 p=subprocess.run([G,*a,'--project='+P,'--format=json'],text=True,capture_output=True,timeout=90)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def collect():
 execution=json.loads((R/'results/execution.json').read_text())['name'].split('/')[-1]
 st=gc('workflows','executions','describe',execution,'--workflow=fds-gpu29-test02','--location=us-central1');(R/'results/status.json').write_text(json.dumps(st,indent=2))
 if st['state']=='ACTIVE':return False
 inventory={n:gc(*args,'--filter=labels.trial_id=gpu29-test02') for n,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
 (R/'results/cleanup.json').write_text(json.dumps(inventory,indent=2));assert not any(inventory.values()),'Cloud cleanup incomplete'
 subprocess.run([G,'storage','cp','--recursive','gs://'+P+'-trial/gpu29/test02/',str(R/'data')],check=True)
 b=json.loads((R/'budget.json').read_text());b['state']='terminal_cleanup_verified';b['completion_unix']=time.time();(R/'budget.json').write_text(json.dumps(b,indent=2));print('COMPLETE',st['state'],flush=True);return True
if __name__=='__main__':
 import sys
 with (R/'data/collector.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   if collect() or '--once' in sys.argv:break
   time.sleep(45)
