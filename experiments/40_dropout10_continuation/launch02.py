"""One guarded controller execution; three separately reserved Spot candidates."""
from pathlib import Path
import sys,json,hashlib,fcntl,time,subprocess,yaml
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,PROJECT,BUCKET,B
O=R/'results02';D=R/'data/training02';WF='fds-gpu40-pool02'
def save(n,x):(O/n).write_text(json.dumps(x,indent=2)+'\n')
with (R/'data/launch.lock').open('a') as guard:
 fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (O/'submission-intent.json').exists(),'Reconcile existing intent; never resubmit'
 assert not gc('workflows','executions','list',WF,'--location=us-central1'),'Existing controller execution; reconcile'
 assert json.loads((R/'results/pool-closed.json').read_text())['passed']
 p=json.loads((O/'package.json').read_text())
 assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
 assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==yaml.safe_load((R/'pool02.yaml').read_text())
 assert not gc('compute','instances','list'),'Unexpected existing worker; reconcile global quota first'
 for c in p['candidates']:
  for z in c['zones']:
   assert gc('compute','accelerator-types','describe','nvidia-tesla-t4','--zone='+z)['name']=='nvidia-tesla-t4'
  q={v['metric']:v['limit']-v['usage'] for v in gc('compute','regions','describe',c['region'])['quotas']}
  assert q['PREEMPTIBLE_NVIDIA_T4_GPUS']>=1 and q['CPUS']>=4 and q['SSD_TOTAL_GB']>=60 and q['IN_USE_ADDRESSES']>=1
  assert not gc('batch','jobs','list','--location='+c['region'],'--filter=labels.trial_id='+c['label'])
 probe=gc('workflows','execute',WF+'-check','--location=us-central1');save('readiness-execution.json',probe)
 for _ in range(45):
  x=gc('workflows','executions','describe',probe['name'].rsplit('/',1)[-1],'--workflow='+WF+'-check','--location=us-central1')
  if x['state']!='ACTIVE':break
  time.sleep(2)
 save('readiness.json',x);assert x['state']=='SUCCEEDED',x
 with (B.parent/'data/budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());amount=p['allowance_per_candidate_usd'];total=b['estimated_spend_usd']+b['reserved_usd']+3*amount;assert total<=b['authorized_usd']
  for c in p['candidates']:
   key='dropout40-pool02-'+c['id'];assert key not in b['reservations']
   b['reservations'][key]=dict(state='reserved_before_upload',allowance_usd=amount,reserved_unix=time.time(),workflow=WF,scope='One gated SpotT4 race candidate;13h VM max at conservative0.75/hour plus0.70 margin; no automatic retries')
  b['reserved_usd']+=3*amount;B.write_text(json.dumps(b,indent=2)+'\n');save('budget-reservation.json',dict(total_with_reservations=total,allowance_per_candidate=amount,cap=b['authorized_usd']))
 uri='gs://'+BUCKET+'/'+p['prefix']+'inputs.tar'
 subprocess.run([G,'storage','cp','--if-generation-match=0',str(D/'inputs.tar'),uri],check=True,capture_output=True)
 m=gc('storage','objects','describe',uri);h=gc('storage','hash',str(D/'inputs.tar'))[0]
 assert int(m['size'])==p['input_bytes'] and m['md5_hash']==h['md5_hash'];save('upload.json',m)
 condition=dict(title='dropout40-pool02-read',description='Race input and ownership grant only',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+p['prefix']+"')");save('read-condition.json',condition)
 subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(O/'read-condition.json')],check=True,capture_output=True)
 save('submission-intent.json',dict(workflow=WF,unix=time.time(),input_sha256=p['input_sha256'],workflow_sha256=p['workflow_sha256']))
 e=gc('workflows','execute',WF,'--location=us-central1');save('execution.json',e)
 with (B.parent/'data/budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text())
  for c in p['candidates']:b['reservations']['dropout40-pool02-'+c['id']].update(state='submitted',execution=e['name'])
  B.write_text(json.dumps(b,indent=2)+'\n')
 print(json.dumps(e),flush=True)
