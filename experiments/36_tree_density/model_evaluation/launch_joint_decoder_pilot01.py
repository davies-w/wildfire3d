"""Single guarded submission of the bounded CUDA timing preflight."""
import re,argparse,base64,datetime,fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,B,PROJECT,BUCKET,gc,read,save
KEY='density36-joint-decoder-pilot01';WF='fds-gpu36-joint01';LABEL='gpu36-joint01'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--resume-verified-upload',action='store_true');args=ap.parse_args();assert not args.resume_verified_upload or args.execute
 with (R/'data/joint-decoder-pilot01-launch.lock').open('w') as own:
  fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
  p=read('results/joint-decoder-pilot01-prepared.json');folder=R/'data/joint-decoder-pilot01'
  assert hashlib.sha256((folder/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
  assert hashlib.sha256((folder/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
  assert read('results/joint-decoder-pilot01-offline-preflight.json')['passed']
  assert read('results/joint-decoder-pilot01-offline-preflight.json')['worker_sha256']==p['files']['worker.py']
  for n,h in p['files'].items():assert hashlib.sha256((folder/n).read_bytes()).hexdigest()==h
  assert not (R/'results/joint-decoder-pilot01-execution.json').exists(),'Existing submission; inspect, never repeat'
  assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF),'Existing workflow: reconcile unknown outcomes first'
  inventory={k:gc(*cmd) for k,cmd in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list')}.items()}
  assert not inventory['instances'],'A GPU VM became active; do not compete or alter the queue'
  for job in inventory['jobs']:
   assert bool(re.search(r'/fds-gpu36-flex01-r[1-9]$',job['name'])) and job['status']['state'] in ('QUEUED','SCHEDULED'),job
  regional={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-central1')['quotas']}
  globalq={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']}
  for metric,minimum in {'NVIDIA_L4_GPUS':1,'CPUS':4,'IN_USE_ADDRESSES':1,'SSD_TOTAL_GB':60}.items():assert regional.get(metric,0)>=minimum,(metric,regional.get(metric))
  assert globalq.get('GPUS_ALL_REGIONS',0)>=1 and globalq.get('CPUS_ALL_REGIONS',0)>=4,globalq
  save('results/joint-decoder-pilot01-readiness.json',dict(passed=True,inventory=inventory,regional_available=regional,global_available=globalq))
  if not args.execute:print('READINESS PASSED; no submission');return
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());allowance=p['maximum_allowance_usd']
   if args.resume_verified_upload:
    r=b['reservations'][KEY];assert r['state']=='reserved_before_upload' and r['workflow']==WF and r['allowance_usd']==allowance
    assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
   else:
    assert KEY not in b['reservations'];assert b['estimated_spend_usd']+b['reserved_usd']+allowance<=b['authorized_usd']
    b['reserved_usd']+=allowance;b['reservations'][KEY]=dict(state='reserved_before_upload',allowance_usd=allowance,reserved_unix=time.time(),scope='Authorized bounded four-output decoder repair, max0.25USD, no automatic retries',workflow=WF)
    B.write_text(json.dumps(b,indent=2)+'\n')
  uri='gs://'+BUCKET+'/density36/joint-decoder-pilot01/inputs.tar'
  if not args.resume_verified_upload:subprocess.run([G,'storage','cp','--if-generation-match=0',str(folder/'inputs.tar'),uri],check=True,capture_output=True)
  meta=gc('storage','objects','describe',uri);local=gc('storage','hash',str(folder/'inputs.tar'))[0]
  assert int(meta['size'])==p['input_bytes'] and meta['crc32c_hash']==local['crc32c_hash']
  if 'md5_hash' in meta:assert meta['md5_hash']==local['md5_hash']
  save('results/joint-decoder-pilot01-upload.json',meta)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=11700)).strftime('%Y-%m-%dT%H:%M:%SZ')
  condition=dict(title='density36-joint-decoder-pilot01-read',description='Private train/validation-only bounded four-output decoder repair inputs and checkpoint verification',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/density36/joint-decoder-pilot01/')")
  save('results/joint-decoder-pilot01-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/joint-decoder-pilot01-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  gc('workflows','deploy',WF,'--location=us-central1','--source='+str(folder/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==yaml.safe_load((folder/'workflow.yaml').read_text())
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
  result=gc('workflows','execute',WF,'--location=us-central1');save('results/joint-decoder-pilot01-execution.json',result)
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=result['name']);B.write_text(json.dumps(b,indent=2)+'\n')
  print('SUBMITTED',result['name'])
if __name__=='__main__':main()
