"""Finish interrupted preflight after diagnosing duplicate readiness step; no new reservation."""
from pathlib import Path
import sys,json,hashlib,fcntl,time,subprocess,datetime,yaml
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,PROJECT,BUCKET,B
D=R/'data/training07';WF='fds-gpu38-history07';KEY='history38-training07'
def save(n,v):(R/'results07'/n).write_text(json.dumps(v,indent=2)+'\n')
with (R/'data/launch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (R/'results07/submission-intent.json').exists()
 assert not (R/'results07/execution.json').exists()
 assert not any(x['name'].endswith('/'+WF) for x in gc('workflows','list','--location=us-central1'))
 b=json.loads(B.read_text());assert b['reservations'][KEY]['state']=='reserved_before_upload'
 assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
 p=json.loads((R/'results07/package.json').read_text());assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
 assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
 assert json.loads((R/'results07/offline-check.json').read_text())['passed']
 m=gc('storage','objects','describe','gs://'+BUCKET+'/history38/training07/inputs.tar');assert m['generation']==json.loads((R/'results07/upload.json').read_text())['generation']
 sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
 # Verify controller can inventory both allowed zones before any GPU job creation.
 checks=[]
 for zone in ['us-central1-c']:
  for resource in ['instances','disks']:
   checks.append({zone.replace('-','_')+'_'+resource:{'call':'http.get','args':{'url':'https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/'+zone+'/'+resource,'auth':{'type':'OAuth2'}},'result':'inventory'}})
 checks.append({'done':{'return':{'passed':True}}})
 (D/'readiness.yaml').write_text(yaml.safe_dump({'main':{'steps':checks}},sort_keys=False))
 gc('workflows','deploy',WF+'-check','--location=us-central1','--source='+str(D/'readiness.yaml'),'--service-account='+sa)
 probe=gc('workflows','execute',WF+'-check','--location=us-central1');save('controller-check-execution.json',probe)
 for _ in range(30):
  checked=gc('workflows','executions','describe',probe['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1')
  if checked['state']!='ACTIVE':break
  time.sleep(2)
 save('controller-check.json',checked);assert checked['state']=='SUCCEEDED',checked
 gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
 assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==yaml.safe_load((D/'workflow.yaml').read_text())
 assert not gc('workflows','executions','list',WF,'--location=us-central1')
 save('submission-intent.json',dict(workflow=WF,unix=time.time(),package=p))
 with (B.parent/'data/budget.lock').open('a') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 result=gc('workflows','execute',WF,'--location=us-central1');save('execution.json',result)
 with (B.parent/'data/budget.lock').open('a') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=result['name']);B.write_text(json.dumps(b,indent=2)+'\n')
 print(json.dumps(result))
