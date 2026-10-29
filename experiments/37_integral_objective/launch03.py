"""Guarded one-time launch, immutable private input, locked cumulative budget."""
from pathlib import Path
import sys,json,hashlib,fcntl,time,subprocess,datetime,yaml
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,PROJECT,BUCKET,B
D=R/'data/training03';WF='fds-gpu37-integral03';KEY='integral37-training03'
def save(n,v):(R/'results03'/n).write_text(json.dumps(v,indent=2)+'\n')
with (R/'data/launch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (R/'results03/submission-intent.json').exists(),'Reconcile existing submission intent; never retry blindly'
 p=json.loads((R/'results03/package.json').read_text())
 assert json.loads((R/'results03/offline-check.json').read_text())['passed']
 assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
 assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
 assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF)
 inv={k:gc(*a) for k,a in dict(instances=('compute','instances','list'),disks=('compute','disks','list'),jobs=('batch','jobs','list','--location=us-west4')).items()};assert all(v==[] for v in inv.values()),inv
 quota={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']};assert quota['GPUS_ALL_REGIONS']>=1
 reg={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-west4')['quotas']}
 for k,v in dict(NVIDIA_L4_GPUS=1,CPUS=4,SSD_TOTAL_GB=60,IN_USE_ADDRESSES=1).items():assert reg[k]>=v
 save('readiness.json',dict(passed=True,inventory=inv,global_available=quota,regional_available=reg))
 with (B.parent/'data/budget.lock').open('a') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());assert KEY not in b['reservations'];assert b['reservations']['integral37-training02']['state']=='submitted';assert json.loads((R/'results02/no-allocation-proof.json').read_text())['passed'];oldexec=json.loads((R/'results02/execution.json').read_text())['name'];assert gc('workflows','executions','describe',oldexec.rsplit('/',1)[1],'--workflow=fds-gpu37-integral02','--location=us-central1')['state']=='SUCCEEDED';b['reservations']['integral37-training02'].update(state='cancelled_reassigned',reassigned_to=KEY,cost=dict(stage='verified_no_vm_allocation',usd=0));b['reserved_usd']-=20.8;assert b['estimated_spend_usd']+b['reserved_usd']+20.8<=b['authorized_usd']
  b['reservations'][KEY]=dict(state='reserved_before_upload',allowance_usd=20.8,reserved_unix=time.time(),scope='Single gated integral-objective rotation0, same8 training folds,16.5h VM max at1.20/h plus0.40 margin, no automatic retries',workflow=WF);b['reserved_usd']+=20.8;B.write_text(json.dumps(b,indent=2)+'\n')
 uri='gs://'+BUCKET+'/integral37/training03/inputs.tar';subprocess.run([G,'storage','cp','--if-generation-match=0',str(D/'inputs.tar'),uri],check=True,capture_output=True)
 m=gc('storage','objects','describe',uri);h=gc('storage','hash',str(D/'inputs.tar'))[0];assert int(m['size'])==p['input_bytes'] and m['crc32c_hash']==h['crc32c_hash'] and m.get('md5_hash')==h.get('md5_hash');save('upload.json',m)
 expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=20)).strftime('%Y-%m-%dT%H:%M:%SZ')
 c=dict(title='integral37-training03-read',description='Private integral objective training inputs and checkpoint verification',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/integral37/training03/')");save('read-condition.json',c)
 subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results03/read-condition.json')],check=True,capture_output=True)
 sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
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
