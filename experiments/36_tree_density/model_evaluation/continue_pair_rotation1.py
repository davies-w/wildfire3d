"""Diagnosed handoff repair: launch only previously unstarted rotation1, once."""
from pathlib import Path
import sys,json,yaml,subprocess,fcntl,hashlib,base64,datetime,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,PROJECT,BUCKET,B,gc,read,save
WF='fds-gpu36-pair-rotation1';PREFIX='density36/pair-sequence01/rotation1/';D=R/'data/pair-rotation1-continuation'
def main():
 with (R/'data/pair-sequence-launch.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (R/'results/pair-rotation1-execution.json').exists()
  assert not (R/'results/pair-rotation1-submission-intent.json').exists(),'Unknown submission outcome must be reconciled, never blindly retried'
  old=read('results/pair-sequence-execution.json')['name'].split('/')
  state=gc('workflows','executions','describe',old[-1],'--workflow='+old[-3],'--location=us-central1')
  assert state['state']=='FAILED' and 'batch.jobs.list' in state['error']['payload'] and 'check_jobs' in state['error']['context']
  assert read('results/pair-sequence-r0-collected.json')['passed']
  completed=gc('storage','objects','describe','gs://'+BUCKET+'/density36/pair-sequence01/rotation0/complete.json')
  cutoff=datetime.datetime.fromisoformat('2026-10-27T15:00:00+00:00')
  created=completed.get('creation_time',completed.get('timeCreated'));assert created and datetime.datetime.fromisoformat(created.replace('Z','+00:00'))<cutoff
  inventory={k:gc(*v) for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inventory.values())
  names=subprocess.run([G,'storage','ls','gs://'+BUCKET+'/'+PREFIX],check=True,capture_output=True,text=True).stdout.splitlines();assert {n.rsplit('/',1)[-1] for n in names}=={'inputs.tar'},names
  assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF),'Reconcile deployment before retry'
  regional={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-central1')['quotas']};glob={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']};assert regional['NVIDIA_L4_GPUS']>=1 and regional['CPUS']>=4 and glob['GPUS_ALL_REGIONS']>=1
  b=json.loads(B.read_text());reservation=b['reservations']['density36-pair-sequence01'];assert reservation['state']=='submitted' and reservation['allowance_usd']==30.4 and b['estimated_spend_usd']+b['reserved_usd']<=125
  package=R/'data/pair-sequence/rotation1/inputs.tar';meta=gc('storage','objects','describe','gs://'+BUCKET+'/'+PREFIX+'inputs.tar');assert meta['md5_hash']==base64.b64encode(hashlib.md5(package.read_bytes()).digest()).decode()
  assert hashlib.sha256(package.read_bytes()).hexdigest()==read('results/pair-sequence-prepared.json')['packages'][1]['input_sha256']
  condition=read('results/pair-sequence-read-condition.json');expiry=condition['expression'].split("timestamp('")[1].split("')")[0];assert (datetime.datetime.fromisoformat(expiry.replace('Z','+00:00'))-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>19*3600
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  w=yaml.safe_load((R/'data/pair-sequence/rotation1/workflow.yaml').read_text())
  # Same proven single-job watchdog used successfully for rotation0. No regional Batch list call.
  assert 'batch.googleapis.com' in json.dumps(w) and 'check_jobs' not in json.dumps(w)
  lease={'claim':{'call':'http.post','args':{'url':'https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o','query':{'uploadType':'media','name':PREFIX+'continuation-lease.json','ifGenerationMatch':0},'auth':{'type':'OAuth2'},'headers':{'Content-Type':'application/json'},'body':{'workflow':WF,'rotation':1,'reason':'Original first pair completed before cutoff; handoff denied batch.jobs.list; no training repeated'}}}}
  w['main']['steps'].insert(0,lease);D.mkdir(exist_ok=True);(D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
  # Exercise controller read/list permissions in cloud before allocating any GPU.
  check={'main':{'steps':[{'instances':{'call':'http.get','args':{'url':'https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-central1-c/instances','auth':{'type':'OAuth2'}},'result':'v'}},{'input':{'call':'http.get','args':{'url':'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/density36%2Fpair-sequence01%2Frotation1%2Finputs.tar','auth':{'type':'OAuth2'}},'result':'p'}},{'done':{'return':{'passed':True,'input_size':'${p.body.size}','instances':'${map.get(v.body,"items")}'}}}]}}
  (D/'readiness.yaml').write_text(yaml.safe_dump(check,sort_keys=False));gc('workflows','deploy',WF+'-check','--location=us-central1','--source='+str(D/'readiness.yaml'),'--service-account='+sa)
  x=gc('workflows','execute',WF+'-check','--location=us-central1');save('results/pair-rotation1-readiness-execution.json',x)
  for _ in range(30):
   q=gc('workflows','executions','describe',x['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1')
   if q['state']!='ACTIVE':break
   time.sleep(2)
  assert q['state']=='SUCCEEDED',q
  save('results/pair-rotation1-readiness.json',dict(cloud=q,inventory=inventory,original_failure=state,first_pair_completed=completed,budget_total=b['estimated_spend_usd']+b['reserved_usd'],existing_reservation_reused=True,recipe_unchanged=True))
  gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==w
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  save('results/pair-rotation1-submission-intent.json',dict(state='submission_pending',workflow=WF,source_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()))
  execution=gc('workflows','execute',WF,'--location=us-central1');save('results/pair-rotation1-execution.json',execution)
  print('SUBMITTED ONCE',execution['name'])
if __name__=='__main__':main()
