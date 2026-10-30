"""One-time user-authorized Iowa queue, bounded separately, arbitration in cloud."""
from pathlib import Path
import sys,json,hashlib,fcntl,time,subprocess,yaml,ast
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,PROJECT,BUCKET,B
D=R/'data/training04';O=R/'results04';WF='fds-gpu38-history04';KEY='history38-training04'
def save(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
with (R/'data/launch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (O/'submission-intent.json').exists(),'Reconcile intent; NEVER duplicate execution'
 p=json.loads((O/'package.json').read_text());old=json.loads((R/'results03/package.json').read_text())
 assert p['resume_sha256']==old['resume_sha256'] and p['resume_epoch']==27
 for n,h in p['files'].items():
  assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
  if n!='runtime.py':assert h==old['files'][n]
 for f in D.glob('*.py'):ast.parse(f.read_text())
 assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
 assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
 w=yaml.safe_load((D/'workflow.yaml').read_text());job=w['main']['steps'][0]['initialize']['assign'][0]['job']
 assert job['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT'
 assert len(job['allocationPolicy']['location']['allowedLocations'])==4
 assert 'oregon_cleanup_verified' in (D/'bootstrap.py').read_text()
 assert not gc('workflows','executions','list',WF,'--location=us-central1') if (O/'workflow-deployed.json').exists() else True
 q={x['metric']:x for x in gc('compute','project-info','describe')['quotas']};assert q['GPUS_ALL_REGIONS']['limit']==1
 region={x['metric']:x for x in gc('compute','regions','describe','us-central1')['quotas']}
 for k,v in {'PREEMPTIBLE_NVIDIA_T4_GPUS':1,'PREEMPTIBLE_CPUS':4,'SSD_TOTAL_GB':60,'IN_USE_ADDRESSES':1}.items():assert region[k]['limit']-region[k]['usage']>=v
 assert not gc('compute','instances','list','--filter=labels.trial_id=gpu38-history04')
 assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu38-history04')
 save('offline-check.json',dict(passed=True,all_model_recipe_data_hashes_identical=True,checkpoint_sha256=p['resume_sha256'],no_local_optimizer=True,private_prefix=True,spot=True,global_gpu_limit=1))
 sa=gc('workflows','describe','fds-gpu38-history03','--location=us-central1')['serviceAccount']
 # Cloud preflight exercises arbitration(false): read only, never deletes or submits.
 checks=[{'read_original':{'call':'arbitrate','args':{'new_allocated':False},'result':'choice'}}]
 for z in 'abcf':
  for resource in ['instances','disks']:
   checks.append({'read_'+z+'_'+resource:{'call':'http.get','args':{'url':'https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-central1-'+z+'/'+resource,'auth':{'type':'OAuth2'}},'result':'inventory'}})
 checks.append({'done':{'return':{'passed':True,'choice':'${choice}'}}})
 (D/'readiness.yaml').write_text(yaml.safe_dump({'main':{'steps':checks},'arbitrate':w['arbitrate']},sort_keys=False))
 gc('workflows','deploy',WF+'-check','--location=us-central1','--source='+str(D/'readiness.yaml'),'--service-account='+sa)
 e=gc('workflows','execute',WF+'-check','--location=us-central1');save('controller-check-execution.json',e)
 for _ in range(30):
  ck=gc('workflows','executions','describe',e['name'].rsplit('/',1)[-1],'--workflow='+WF+'-check','--location=us-central1')
  if ck['state']!='ACTIVE':break
  time.sleep(2)
 save('controller-check.json',ck);assert ck['state']=='SUCCEEDED',ck
 assert json.loads(ck['result'])['choice']['winner']=='waiting','Oregon already allocated: no extra queue needed'
 # Compilation of the complete workflow happens before reserving/uploading/submitting.
 gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
 deployed=gc('workflows','describe',WF,'--location=us-central1');assert yaml.safe_load(deployed['sourceContents'])==w;save('workflow-deployed.json',dict(revision=deployed['revisionId']))
 assert not gc('workflows','executions','list',WF,'--location=us-central1')
 with (B.parent/'data/budget.lock').open('a') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());assert KEY not in b['reservations']
  total=b['estimated_spend_usd']+b['reserved_usd']+17.7;assert total<=b['authorized_usd']
  b['reservations'][KEY]=dict(state='reserved_before_upload',allowance_usd=17.7,reserved_unix=time.time(),workflow=WF,scope='User-authorized regional Spot T4 race, separate22.5h VM bound at0.75/h plus0.825; shared checkpoint, ownership-gated, winner cancels loser')
  b['reserved_usd']+=17.7;B.write_text(json.dumps(b,indent=2)+'\n');save('budget-reservation.json',dict(total_with_reservations=total,allowance=17.7,cap=b['authorized_usd']))
 uri='gs://'+BUCKET+'/history38/training04/inputs.tar';subprocess.run([G,'storage','cp','--if-generation-match=0',str(D/'inputs.tar'),uri],check=True,capture_output=True)
 m=gc('storage','objects','describe',uri);h=gc('storage','hash',str(D/'inputs.tar'))[0];assert int(m['size'])==p['input_bytes'] and m['md5_hash']==h['md5_hash'];save('upload.json',m)
 c=dict(title='history38-training04-read',description='Private Iowa continuation inputs and ownership grant',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/history38/training04/')");save('read-condition.json',c)
 subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(O/'read-condition.json')],check=True,capture_output=True)
 save('submission-intent.json',dict(workflow=WF,unix=time.time(),package=p))
 with (B.parent/'data/budget.lock').open('a') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 e=gc('workflows','execute',WF,'--location=us-central1');save('execution.json',e)
 with (B.parent/'data/budget.lock').open('a') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n')
 print(json.dumps(e),flush=True)
