"""Finish diagnosed pre-submit CLI syntax interruption, never re-reserve or retry execute."""
import base64,fcntl,hashlib,json,sys
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,B,BUCKET,gc,read,save
WF='fds-gpu36-preflight01';KEY='density36-model-preflight01'
def main():
 with (R/'data/model-timing-launch.lock').open('w') as own:
  fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (R/'results/model-timing-execution.json').exists()
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  assert not gc('batch','jobs','list','--location=us-central1') and not gc('compute','instances','list')
  folder=R/'data/model-timing';p=read('results/model-timing-prepared.json')
  assert hashlib.sha256((folder/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
  assert hashlib.sha256((folder/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==yaml.safe_load((folder/'workflow.yaml').read_text())
  meta=gc('storage','objects','describe','gs://'+BUCKET+'/density36/model-preflight01/inputs.tar')
  assert int(meta['size'])==p['input_bytes'] and meta['md5_hash']==base64.b64encode(hashlib.md5((folder/'inputs.tar').read_bytes()).digest()).decode()
  policy=gc('storage','buckets','get-iam-policy','gs://'+BUCKET);condition=read('results/model-timing-read-condition.json')
  assert any(b.get('condition')==condition and b['role']=='roles/storage.objectViewer' and 'serviceAccount:fds-worker@tmrw-wildfire-20261015.iam.gserviceaccount.com' in b['members'] for b in policy['bindings'])
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['reservations'][KEY]['state']=='reserved_before_upload' and b['reservations'][KEY]['allowance_usd']==.5
   assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
   save('results/model-timing-setup-repair.json',{'reason':'Execution-list CLI flag rejected before execute; corrected to positional workflow','previous_executions':[],'deployed_source_exact':True,'input_md5_verified':True,'new_reservation':False})
   b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
  e=gc('workflows','execute',WF,'--location=us-central1');save('results/model-timing-execution.json',e)
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n')
  print('SUBMITTED',e['name'])
if __name__=='__main__':main()
