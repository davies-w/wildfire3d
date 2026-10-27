"""Final guarded launch, only after cloud fixtures and DVC archival pass."""
from pathlib import Path
import json,sys,fcntl,hashlib,time,yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,gc,read,save
WF='fds-gpu36-flex-queue01';KEY='density36-flex-queue01';D=R/'data/flex-queue'
def main():
 with (R/'data/flex-queue-launch.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (R/'results/flex-queue-execution.json').exists() and not (R/'results/flex-queue-submission-intent.json').exists()
  p=read('results/flex-queue-prepared.json');assert read('results/flex-queue-checks.json')['passed'];assert read('results/flex-queue-readiness.json')['state']=='SUCCEEDED'
  assert read('results/flex-queue-archive.json')['mirror_pushed'];assert read('results/flex-watchdog-checks.json')['passed']
  assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
  deployed=gc('workflows','describe',WF,'--location=us-central1');assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((D/'workflow.yaml').read_text())
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  inv={k:gc(*v) for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inv.values())
  with (B.parent/'data/budget.lock').open('w') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());assert KEY not in b['reservations'];assert b['estimated_spend_usd']+b['reserved_usd']+40<=125
   b['reservations'][KEY]=dict(state='submission_pending',allowance_usd=40,reserved_unix=time.time(),scope='User-authorized fixed remaining rotations1..9, matched plain/gated, Flex-start sequential queue; per-pair15.2 gate, 24h allocation wait, no automatic retries');b['reserved_usd']+=40;B.write_text(json.dumps(b,indent=2)+'\n');save('results/flex-queue-budget.json',dict(estimate=b['estimated_spend_usd'],reserved=b['reserved_usd'],total=b['estimated_spend_usd']+b['reserved_usd'],cap=125))
  save('results/flex-queue-submission-intent.json',dict(workflow=WF,state='submission_pending',source_sha256=p['workflow_sha256']))
  e=gc('workflows','execute',WF,'--location=us-central1');save('results/flex-queue-execution.json',e)
  with (B.parent/'data/budget.lock').open('w') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n')
  print('SUBMITTED ONCE',e['name'])
if __name__=='__main__':main()
