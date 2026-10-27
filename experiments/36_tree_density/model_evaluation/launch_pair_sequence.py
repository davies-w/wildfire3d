"""Reserve/upload/deploy, validate octet-stream gates in cloud, execute once."""
import sys,json,hashlib,base64,subprocess,fcntl,time,datetime,yaml
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,PROJECT,BUCKET,B,gc,read,save
D=R/'data/pair-sequence';WF='fds-gpu36-pair-sequence01';KEY='density36-pair-sequence01'
def main():
 with (R/'data/pair-sequence-launch.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);p=read('results/pair-sequence-prepared.json')
  assert not (R/'results/pair-sequence-execution.json').exists()
  assert not gc('workflows','list','--location=us-central1','--filter=name:'+WF),'Existing deployment: reconcile before resuming setup'
  assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
  for pkg in p['packages']:assert hashlib.sha256((D/f"rotation{pkg['rotation']}"/'inputs.tar').read_bytes()).hexdigest()==pkg['input_sha256']
  inv={k:gc(*v) for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inv.values());save('results/pair-sequence-readiness.json',{'inventory':inv})
  regional={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-central1')['quotas']};glob={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']};assert regional['NVIDIA_L4_GPUS']>=1 and regional['CPUS']>=4 and glob['GPUS_ALL_REGIONS']>=1 and glob['CPUS_ALL_REGIONS']>=4
  with (B.parent/'data/budget.lock').open('w') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());assert KEY not in b['reservations']
   for old,stem in [('density36-pair-training01','model-pair-training'),('density36-model-pair-preflight01','model-pair-timing')]:
    r=b['reservations'][old];assert r['cost']['stage'] in ('runtime_estimate','posted_billing_subject_to_adjustment') and r['cost']['usd']>0
    assert read('results/'+stem+'-cleanup.json')=={'jobs':[],'instances':[],'disks':[]};assert read('results/'+stem+'-status.json')['state'] in ('SUCCEEDED','FAILED');r['state']='completed_reconciled'
   b['reserved_usd']=sum(r['allowance_usd'] for r in b['reservations'].values() if r['state'] in ('reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue'))
   assert b['estimated_spend_usd']+b['reserved_usd']+30.4<=125
   b['reservations'][KEY]=dict(state='reserved_before_upload',allowance_usd=30.4,reserved_unix=time.time(),scope='Explicitly authorized repaired rotation0 pair and conditional rotation1 before08Pacific; two15.2maxbounds, zero retries');b['reserved_usd']+=30.4;B.write_text(json.dumps(b,indent=2)+'\n');save('results/pair-sequence-budget.json',dict(estimate=b['estimated_spend_usd'],reserved=b['reserved_usd'],total=b['estimated_spend_usd']+b['reserved_usd'],maximum=125))
  uploads={}
  for pkg in p['packages']:
   path=D/f"rotation{pkg['rotation']}"/'inputs.tar';uri='gs://'+BUCKET+'/'+pkg['prefix']+'inputs.tar';subprocess.run([G,'storage','cp','--if-generation-match=0',str(path),uri],check=True,capture_output=True);m=gc('storage','objects','describe',uri);assert int(m['size'])==path.stat().st_size and m['md5_hash']==base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode();uploads[uri]=m
  fixture=R/'results/pair-sequence-gate-fixture.json';fixture.write_text(json.dumps({'success':True,'folds':2,'selected':[{'fold':0},{'fold':1}],'test_not_evaluated_yet':True}));subprocess.run([G,'storage','cp','--content-type=application/octet-stream','--if-generation-match=0',str(fixture),'gs://'+BUCKET+'/density36/pair-sequence01/gate-fixture.json'],check=True,capture_output=True);save('results/pair-sequence-uploads.json',uploads)
  sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=36)).strftime('%Y-%m-%dT%H:%M:%SZ')
  c=dict(title='density36-pair-sequence01-read',description='Bounded two-rotation cloud supervisor and worker private inputs',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/density36/pair-sequence01/')");save('results/pair-sequence-read-condition.json',c)
  for member in ('fds-worker@'+PROJECT+'.iam.gserviceaccount.com',sa.split('/')[-1]):subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:'+member,'--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/pair-sequence-read-condition.json')],check=True,capture_output=True)
  w=yaml.safe_load((D/'workflow.yaml').read_text());test={'main':{'steps':[{'fetch':{'call':'http.get','args':{'url':'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/density36%2Fpair-sequence01%2Fgate-fixture.json','query':{'alt':'media'},'auth':{'type':'OAuth2'}},'result':'r'}},{'decode':{'call':'decode_document','args':{'value':'${r.body}'},'result':'d'}},{'assert_valid':{'switch':[{'condition':'${d.success != true or d.folds != 2 or len(d.selected) != 2 or d.test_not_evaluated_yet != true}','raise':'Decode gate failed'}]}},{'map_decode':{'call':'decode_document','args':{'value':'${d}'},'result':'d2'}},{'done':{'return':{'passed':True,'decoded':'${d2}','no_compute':True}}}]},'decode_document':w['decode_document']};(R/'results/pair-sequence-gate-check.yaml').write_text(yaml.safe_dump(test,sort_keys=False))
  gc('workflows','deploy',WF+'-check','--location=us-central1','--source='+str(R/'results/pair-sequence-gate-check.yaml'),'--service-account='+sa)
  check=gc('workflows','execute',WF+'-check','--location=us-central1');save('results/pair-sequence-gate-check-execution.json',check)
  for _ in range(30):
   q=gc('workflows','executions','describe',check['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1')
   if q['state']!='ACTIVE':break
   time.sleep(2)
  save('results/pair-sequence-gate-check.json',q);assert q['state']=='SUCCEEDED' and json.loads(q['result'])['passed'],q
  gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
  assert yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])==w
  assert not gc('workflows','executions','list',WF,'--location=us-central1')
  with (B.parent/'data/budget.lock').open('w') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
  execution=gc('workflows','execute',WF,'--location=us-central1');save('results/pair-sequence-execution.json',execution)
  with (B.parent/'data/budget.lock').open('w') as bl:
   fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][KEY].update(state='submitted',execution=execution['name']);B.write_text(json.dumps(b,indent=2)+'\n')
  print('SUBMITTED ONCE',execution['name'])
if __name__=='__main__':main()
