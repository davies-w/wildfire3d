"""Replace only the supervisor; keep the same Batch job and queued request."""
from pathlib import Path
import sys,json,yaml,fcntl,time,subprocess
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,PROJECT,BUCKET,B
WF='fds-gpu37-integral03-wait';JOB='fds-gpu37-integral03';D=R/'data/wait-supervisor';D.mkdir(exist_ok=True)
def save(n,v):(R/'results03'/n).write_text(json.dumps(v,indent=2)+'\n')
with (R/'data/adopt-wait.lock').open('a') as own:
 fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (R/'results03/wait-submission-intent.json').exists(),'Reconcile existing handoff; no blind repeat'
 old=json.loads((R/'results03/execution.json').read_text());old_id=old['name'].rsplit('/',1)[1]
 current=gc('workflows','executions','describe',old_id,'--workflow='+JOB,'--location=us-central1');assert current['state']=='ACTIVE',current['state']
 job=gc('batch','jobs','describe',JOB,'--location=us-west4');assert job['status']['state'] in ['QUEUED','SCHEDULED','RUNNING'];uid=job['uid']
 w=yaml.safe_load((R/'data/training03/workflow.yaml').read_text());steps=w['main']['steps']
 steps[0]={'initialize':{'assign':[{'status':{'body':{'status':{'state':'UNKNOWN'}}}}]}}
 # Adopt existing job with GET. There is no create/post Batch call in this workflow.
 steps[1]={'adopt':{'call':'http.get','args':{'url':'https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/us-west4/jobs/'+JOB,'auth':{'type':'OAuth2'}},'result':'created'}}
 steps.insert(2,{'verify_identity':{'switch':[{'condition':'${created.body.uid != "'+uid+'"}','raise':'Existing Batch job identity mismatch'}]}})
 monitor=next(s['monitor'] for s in steps if 'monitor' in s)['try']['steps']
 checks=next(s['check'] for s in monitor if 'check' in s)['switch']
 checks[:]=[x for x in checks if 'deadline' not in x['condition']]
 wait=next(s['wait'] for s in monitor if 'wait' in s)
 wait['args']['seconds']='${if(len(default(map.get(active_vms.body, "items"), [])) == 0, 300, 30)}'
 txt=yaml.safe_dump(w,sort_keys=False);assert 'queue_deadline' not in txt and 'sys.now() >= deadline' not in txt and 'jobId:' not in txt
 assert '+ 59400' in txt
 (D/'workflow.yaml').write_text(txt)
 assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF)
 sa=gc('workflows','describe',JOB,'--location=us-central1')['serviceAccount']
 gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
 assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==w
 assert not gc('workflows','executions','list',WF,'--location=us-central1')
 # Exact-prefix permission remains valid while user-requested queue waits; remove after terminal collection.
 c=dict(title='integral37-training03-wait-read',description='User authorized wait-until-capacity; exact private experiment prefix only; remove after terminal collection',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/integral37/training03/')")
 save('wait-read-condition.json',c)
 subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results03/wait-read-condition.json')],check=True,capture_output=True)
 # Cancel old supervisor only. Cancellation does not delete Batch; new controller adopts it.
 save('wait-submission-intent.json',dict(old_execution=old['name'],workflow=WF,job_uid=uid,unix=time.time(),no_new_batch_job=True))
 gc('workflows','executions','cancel',old_id,'--workflow='+JOB,'--location=us-central1','--quiet')
 stopped=gc('workflows','executions','describe',old_id,'--workflow='+JOB,'--location=us-central1');assert stopped['state']=='CANCELLED'
 assert gc('batch','jobs','describe',JOB,'--location=us-west4')['uid']==uid
 result=gc('workflows','execute',WF,'--location=us-central1');save('wait-execution.json',result)
 with (B.parent/'data/budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations']['integral37-training03']['supervisor_execution']=result['name'];B.write_text(json.dumps(b,indent=2)+'\n')
 save('wait-handoff.json',dict(passed=True,existing_job_uid=uid,old_supervisor_cancelled=True,new_supervisor=result['name'],new_batch_jobs_created=0,queue_timeout_removed=True,vm_runtime_limit_seconds=59400,checkpoint_policy='Every completed epoch uploaded; no checkpoint until first epoch completes'))
 print(json.dumps(result))
