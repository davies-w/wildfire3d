"""Single guarded submission of the bounded CUDA timing preflight."""
import re,argparse,base64,datetime,fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,B,PROJECT,BUCKET,gc,read,save
KEY='density36-canonical-pilot02';WF='fds-gpu36-canonical02';LABEL='gpu36-canonical02'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--resume-verified-upload',action='store_true');args=ap.parse_args();assert not args.resume_verified_upload or args.execute
 with (R/'data/canonical-pilot02-launch.lock').open('w') as own:
  fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
  p=read('results/canonical-pilot02-prepared.json');folder=R/'data/canonical-pilot02'
  assert hashlib.sha256((folder/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
  assert hashlib.sha256((folder/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
  assert read('results/canonical-pilot02-offline-preflight.json')['passed']
  assert read('results/canonical-pilot02-offline-preflight.json')['input_sha256']==p['input_sha256']
  assert read('results/canonical-pilot02-offline-preflight.json')['worker_sha256']==p['files']['worker.py']
  assert read('results/canonical-pilot02-offline-preflight.json')['workflow_sha256']==p['workflow_sha256']
  assert p['maximum_allowance_usd']==1.3
  accounting=read('results/timing-cost-bounds-preflight.json');assert accounting['passed'] and accounting['source_sha256']==hashlib.sha256((R.parents[1]/'scripts/reconcile_runtime_costs.py').read_bytes()).hexdigest()
  prices=read('results/canonical-pilot02-price-bound.json');assert prices['passed'] and prices['conservative_rate_bound_usd_per_hour']==1.2 and prices['maximum_compute_allowance_usd']==1.3
  machine=[]
  for zone in ['us-east4-a','us-east4-c']:
   item=gc('compute','machine-types','describe','g2-standard-4','--zone='+zone);assert item['name']=='g2-standard-4' and item['zone'].endswith(zone) and item['guestCpus']==4 and item['memoryMb']>=12000 and item['accelerators']==[dict(guestAcceleratorCount=1,guestAcceleratorType='nvidia-l4')];machine.append(item)
  previous=read('results/canonical-pilot01-no-allocation-proof.json');assert previous['passed'] and previous['successful_vm_allocations']==0
  assert read('results/canonical-pilot01-cleanup.json')=={'jobs':[],'instances':[],'disks':[]}
  assert read('results/canonical-pilot01-permission-removed.json')['exact_grant_removed']

  from canonical_transfer_guard02 import check_transfer_bound
  save('results/canonical-pilot02-transfer-bound.json',check_transfer_bound(p['input_bytes'],2*1024**3))
  subnet=gc('compute','networks','subnets','describe','fds-timing-east4','--region=us-east4');assert subnet['network'].endswith('/networks/fds-trial') and subnet['ipCidrRange']=='10.43.0.0/24' and subnet['privateIpGoogleAccess'] is True
  for n,h in p['files'].items():assert hashlib.sha256((folder/n).read_bytes()).hexdigest()==h
  assert not (R/'results/canonical-pilot02-execution.json').exists(),'Existing submission; inspect, never repeat'
  assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF),'Existing workflow: reconcile unknown outcomes first'
  inventory={k:gc(*cmd) for k,cmd in {'jobs':('batch','jobs','list','--location=us-east4'),'instances':('compute','instances','list')}.items()}
  assert not inventory['instances'],'A GPU VM became active; do not compete or alter the queue'
  for job in inventory['jobs']:
   assert bool(re.search(r'/fds-gpu36-flex01-r[1-9]$',job['name'])) and job['status']['state'] in ('QUEUED','SCHEDULED'),job
  regional={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-east4')['quotas']}
  globalq={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']}
  for metric,minimum in {'NVIDIA_L4_GPUS':1,'CPUS':4,'IN_USE_ADDRESSES':1,'SSD_TOTAL_GB':60}.items():assert regional.get(metric,0)>=minimum,(metric,regional.get(metric))
  assert globalq.get('GPUS_ALL_REGIONS',0)>=1 and globalq.get('CPUS_ALL_REGIONS',0)>=4,globalq
  assert next(q['limit'] for q in gc('compute','project-info','describe')['quotas'] if q['metric']=='GPUS_ALL_REGIONS')==1, 'Whole-workflow bound assumes one concurrent standard GPU'
  previous=read('results/guard-matched-pilot04-no-allocation-proof.json');assert previous['passed'] and previous['successful_vm_allocations']==0
  assert read('results/guard-matched-pilot04-cleanup.json')=={'jobs':[],'instances':[],'disks':[]}
  assert read('results/guard-matched-pilot04-permission-removed.json')['exact_grant_removed']
  previous_cost=read('results/guard-matched-pilot04-cost-reconciled.json');assert previous_cost['pilot_compute_cost']['stage']=='verified_no_vm_allocation' and previous_cost['pilot_compute_cost']['usd']==0
  matched=read('results/guard-matched-objective-preflight.json');assert matched['passed']
  for name,digest in matched['source_sha256'].items():
   if name in p['files']:assert p['files'][name]==digest, 'Fixture/package source mismatch: '+name
  assert read('results/canonical-pilot02-offline-preflight.json')['serialized_restore_scope_preserved']
  assert read('results/guard-matched-pilot01-analysis.json')['passed']
  save('results/canonical-pilot02-readiness.json',dict(passed=True,verified_machine_type=machine,inventory=inventory,regional_available=regional,global_available=globalq))
  if not args.execute:print('READINESS PASSED; no submission');return
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());allowance=p['maximum_allowance_usd']
   if args.resume_verified_upload:
    r=b['reservations'][KEY];assert r['state']=='reserved_before_upload' and r['workflow']==WF and r['allowance_usd']==allowance
    assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
   else:
    assert KEY not in b['reservations'];assert b['estimated_spend_usd']+b['reserved_usd']+allowance<=b['authorized_usd']
    b['reserved_usd']+=allowance;b['reservations'][KEY]=dict(state='reserved_before_upload',allowance_usd=allowance,reserved_unix=time.time(),scope='Authorized bounded four-output decoder repair, max1.30USD, no automatic retries',workflow=WF)
    B.write_text(json.dumps(b,indent=2)+'\n')
  uri='gs://'+BUCKET+'/density36/canonical-pilot02/inputs.tar'
  if not args.resume_verified_upload:subprocess.run([G,'storage','cp','--if-generation-match=0',str(folder/'inputs.tar'),uri],check=True,capture_output=True)
  meta=gc('storage','objects','describe',uri);local=gc('storage','hash',str(folder/'inputs.tar'))[0]
  assert int(meta['size'])==p['input_bytes'] and meta['crc32c_hash']==local['crc32c_hash']
  if 'md5_hash' in meta:assert meta['md5_hash']==local['md5_hash']
  save('results/canonical-pilot02-upload.json',meta)
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=11700)).strftime('%Y-%m-%dT%H:%M:%SZ')
  condition=dict(title='density36-canonical-pilot02-read',description='Private train/validation-only bounded four-output decoder repair inputs and checkpoint verification',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/density36/canonical-pilot02/')")
  save('results/canonical-pilot02-read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/canonical-pilot02-read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  gc('workflows','deploy',WF,'--location=us-central1','--source='+str(folder/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==yaml.safe_load((folder/'workflow.yaml').read_text())
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
  result=gc('workflows','execute',WF,'--location=us-central1');save('results/canonical-pilot02-execution.json',result)
  with (B.parent/'data/budget.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=result['name']);B.write_text(json.dumps(b,indent=2)+'\n')
  print('SUBMITTED',result['name'])
if __name__=='__main__':main()
