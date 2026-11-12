"""One immutable cloud submission, guarded by inventory, preservation and private allocation."""
from pathlib import Path
import sys,json,hashlib,fcntl,time,subprocess,datetime,yaml,tarfile,io,base64
R=Path(__file__).resolve().parent;ROOT=R.parents[1];G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud');PROJECT='tmrw-wildfire-20261015';BUCKET=PROJECT+'-trial';B=R.parent/'33_representation_loss/budget.json'
def gc(*args):
 result=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],text=True,capture_output=True,timeout=240)
 if result.returncode:raise RuntimeError(result.stderr)
 return json.loads(result.stdout or '{}')
D=R/'private';WF='fds-fourstate52-training01';PREFIX='fourstate52/training01/';LABEL='fourstate52-training01'
def save(n,x):(D/n).write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert '--launch' in sys.argv,'Use --launch only after authorized preflight'
 with (D/'launch.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (D/'submission-intent.json').exists(),'Reconcile prior intent; never duplicate launch'
  assert json.loads((R/'input-preservation.json').read_text())['passed']
  checked=json.loads((R/'local-check.json').read_text());assert checked['passed']
  for n,h in checked['source_hashes'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
  assert not gc('compute','instances','list'),'Another VM is active; re-evaluate allocation'
  assert not gc('batch','jobs','list','--location=us-west1'),'Another Batch job exists'
  assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF)
  available={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-west1')['quotas']}
  for k,v in dict(PREEMPTIBLE_NVIDIA_T4_GPUS=1,CPUS=4,SSD_TOTAL_GB=60,IN_USE_ADDRESSES=1).items():assert available[k]>=v,(k,available[k])
  globalq={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']};assert globalq['GPUS_ALL_REGIONS']>=1
  p=json.loads((D/'approved-allocation.json').read_text());billing=json.loads((D/'billing.json').read_text());posted=sum(float(c['net_cost']) for c in billing['costs']);assert time.time()-datetime.datetime.fromisoformat(billing['fetched_at_utc']).timestamp()<3600
  assert posted+sum(p[k] for k in ['training_cap_usd','test_reserve_usd','buffer_usd'])<=p['project_cap_usd'];p.update(posted_usd=posted,allocation_not_before_unix=time.time());save('budget-policy.json',p)
  max_seconds=int((p['training_cap_usd']+p['test_reserve_usd'])/p['rate_upper_usd_hour']*3600)
  with (B.parent/'data/budget.lock').open('a') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);ledger=json.loads(B.read_text());assert ledger['authorized_usd']==p['project_cap_usd'];assert WF not in ledger['reservations']
   save('prior-ledger.json',ledger)
   ledger.setdefault('posted_reconciliations',[]).append(dict(unix=time.time(),posted_usd=posted,prior_estimate=ledger['estimated_spend_usd'],prior_reserved=ledger['reserved_usd'],reason='Prior simulation and preservation workers terminal; new user-approved fresh single rotation replaces unused old training reservation. Posted costs plus separate lag buffer.'))
   ledger['estimated_spend_usd']=posted;ledger['reserved_usd']=sum(p[k] for k in ['training_cap_usd','test_reserve_usd','buffer_usd']);ledger['reservations'][WF]=dict(state='reserved_before_upload',allowance_usd=ledger['reserved_usd'],private_policy=str((D/'budget-policy.json').relative_to(ROOT)))
   ledger['active_allocation_keys']=[WF];B.write_text(json.dumps(ledger,indent=2)+'\n')
  names=['worker.py','model.py','objective.py','runtime.py','budget_guard.py','cloud_check.py','coverage-plan.json','data/observations.npz','data/schema.json','private/budget-policy.json'];payload={n:(R/n).read_bytes() for n in names};payload['hashes.json']=json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in payload.items()}).encode()
  with tarfile.open(D/'inputs.tar','w') as tar:
   for n,b in payload.items():
    info=tarfile.TarInfo(n);info.size=len(b);tar.addfile(info,io.BytesIO(b))
  sha=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()
  bootstrap=(R/'bootstrap_template.py').read_text().replace('__INPUT_SHA256__',sha)
  (D/'bootstrap.py').write_text(bootstrap)
  w=yaml.safe_load((R/'workflow_template.yaml').read_text());job=w['main']['steps'][0]['initialize']['assign'][0]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(max_seconds)+'s';task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
  raw=yaml.safe_dump(w,sort_keys=False).replace('fds-gpu38-history01',WF).replace('gpu38-history01',LABEL).replace('history38/training01/',PREFIX).replace('88200',str(max_seconds))
  w=yaml.safe_load(raw);monitor=w['main']['steps'][2]['monitor']['try']['steps'];checks=next(s['check']['switch'] for s in monitor if 'check' in s)
  checks.append(dict(condition='${sys.now() >= '+str(int(p['allocation_not_before_unix'])+max_seconds)+'}',next='record'))
  checks.append(dict(condition='${(status.body.status.state == "QUEUED" or status.body.status.state == "SCHEDULED") and sys.now() >= '+str(int(p['allocation_not_before_unix'])+1800)+'}',next='record'))
  (D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
  uri='gs://'+BUCKET+'/'+PREFIX+'inputs.tar';subprocess.run([G,'storage','cp','--if-generation-match=0',str(D/'inputs.tar'),uri],check=True,capture_output=True)
  obj=gc('storage','objects','describe',uri);local=gc('storage','hash',str(D/'inputs.tar'))[0];assert obj['md5_hash']==local['md5_hash'] and int(obj['size'])==(D/'inputs.tar').stat().st_size
  expiry=datetime.datetime.fromtimestamp(p['allocation_not_before_unix']+max_seconds+3600,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
  condition=dict(title='fourstate52-training01-read',description='Read only this run input and verify its immutable outputs until run deadline',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+PREFIX+"') && request.time < timestamp('"+expiry+"')");save('read-condition.json',condition)
  subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(D/'read-condition.json')],check=True,capture_output=True)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
  gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==w
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  save('submission-intent.json',dict(workflow=WF,unix=time.time(),input_sha256=sha,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
  result=gc('workflows','execute',WF,'--location=us-central1');save('execution.json',result)
  with (B.parent/'data/budget.lock').open('a') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);ledger=json.loads(B.read_text());ledger['reservations'][WF].update(state='submitted',execution=result['name']);B.write_text(json.dumps(ledger,indent=2)+'\n')
  print('Submitted one guarded training workflow:',result['name'])
if __name__=='__main__':main()
