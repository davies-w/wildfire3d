"""Single guarded submission of the bounded CUDA timing preflight."""
import argparse,base64,datetime,fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,B,PROJECT,BUCKET,gc,read,save
KEY='density36-pair-training01';WF='fds-gpu36-pairtrain01';LABEL='gpu36-pairtrain01'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
 with (R/'data/model-pair-training-launch.lock').open('w') as own:
  fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
  p=read('results/model-pair-training-prepared.json');folder=R/'data/model-pair-training'
  assert hashlib.sha256((folder/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
  assert hashlib.sha256((folder/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
  assert read('results/model-pair-timing-collected.json')['passed']
  for n,h in p['files'].items():assert hashlib.sha256((folder/n).read_bytes()).hexdigest()==h
  assert not (R/'results/model-pair-training-execution.json').exists(),'Existing submission; inspect, never repeat'
  assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF),'Existing workflow: reconcile unknown outcomes first'
  inventory={k:gc(*cmd) for k,cmd in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list')}.items()};assert not any(inventory.values())
  regional={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-central1')['quotas']}
  globalq={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']}
  for metric,minimum in {'NVIDIA_L4_GPUS':1,'CPUS':4,'IN_USE_ADDRESSES':1,'SSD_TOTAL_GB':60}.items():assert regional.get(metric,0)>=minimum,(metric,regional.get(metric))
  assert globalq.get('GPUS_ALL_REGIONS',0)>=1 and globalq.get('CPUS_ALL_REGIONS',0)>=4,globalq
  save('results/model-pair-training-readiness.json',dict(passed=True,inventory=inventory,regional_available=regional,global_available=globalq))
  if not args.execute:print('READINESS PASSED; no submission');return
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());assert KEY not in b['reservations']
   allowance=p['maximum_allowance_usd'];assert b['estimated_spend_usd']+b['reserved_usd']+allowance<=b['authorized_usd']
   b['reserved_usd']+=allowance;b['reservations'][KEY]=dict(state='preparing_upload',allowance_usd=allowance,reserved_unix=time.time(),scope='Authorized single rotation0 plain/gated stride-one pair; cloud watchdog; no automatic retries',workflow=WF)
   B.write_text(json.dumps(b,indent=2)+'\n')
  uri='gs://'+BUCKET+'/density36/model-pair-training01/inputs.tar'
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(folder/'inputs.tar'),uri],check=True,capture_output=True)
  meta=gc('storage','objects','describe',uri);assert int(meta['size'])==p['input_bytes'] and meta['md5_hash']==base64.b64encode(hashlib.md5((folder/'inputs.tar').read_bytes()).digest()).decode()
  save('results/model-pair-training-upload.json',meta)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=75600)).strftime('%Y-%m-%dT%H:%M:%SZ')
  condition=dict(title='density36-pair-training01-read',description='Private matched single-split pair training inputs and checkpoint verification',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/density36/model-pair-training01/')")
  save('results/model-pair-training-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/model-pair-training-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  gc('workflows','deploy',WF,'--location=us-central1','--source='+str(folder/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==yaml.safe_load((folder/'workflow.yaml').read_text())
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
  result=gc('workflows','execute',WF,'--location=us-central1');save('results/model-pair-training-execution.json',result)
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=result['name']);B.write_text(json.dumps(b,indent=2)+'\n')
  print('SUBMITTED',result['name'])
if __name__=='__main__':main()
